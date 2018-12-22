import numpy as np

# import fastText as ft

import torch
import torch.nn as nn
from torch.nn import BCEWithLogitsLoss
from torch.autograd import Variable
from expertise import utils

from expertise.evaluators.mean_avg_precision import eval_map
from expertise.evaluators.hits_at_k import eval_hits_at_k

class Model(torch.nn.Module):
    def __init__(self, config, vocab):
        super(Model, self).__init__()

        self.config = config
        self.vocab = vocab

        # if self.config.fasttext:
        #     self.cached_ft = ft.load_model(self.config.fasttext)
        # else:
        #     self.cached_ft = None

        # Keyword embeddings
        self.embedding = nn.Embedding(len(vocab)+1, config.embedding_dim, padding_idx=0)

        # Vector of ones (used for loss)
        if self.config.use_cuda:
            self.ones = Variable(torch.ones(config.batch_size, 1).cuda())
        else:
            self.ones = Variable(torch.ones(config.batch_size, 1))

        self.loss = BCEWithLogitsLoss() # Is this the best loss function, or should we use BPR (sig(pos - neg)) instead?

    def compute_loss(self, query, pos_result, neg_result, query_len, pos_len, neg_len):
        """ Compute the loss (BPR) for a batch of examples
        :param query: Entity mentions
        :param pos_result: True aliases of the Mentions
        :param neg_result: False aliases of the Mentions
        :param query_len: lengths of mentions
        :param pos_len: lengths of positives
        :param neg_len: lengths of negatives
        :return:
        """

        # B by dim
        source_embed = self.embed(query, query_len)
        # B by dim
        pos_embed = self.embed(pos_result, pos_len)
        # B by dim
        neg_embed = self.embed(neg_result, neg_len)
        loss = self.loss(
            utils.row_wise_dot(source_embed , pos_embed )
            - utils.row_wise_dot(source_embed , neg_embed ),
            self.ones)
        return loss

    def score_pair(self, source, target, source_len, target_len):
        """

        :param source: Batchsize by Max_String_Length
        :param target: Batchsize by Max_String_Length
        :return: Batchsize by 1
        """
        source_embed = self.embed_dev(source, source_len)
        target_embed = self.embed_dev(target, target_len)
        scores = utils.row_wise_dot(source_embed, target_embed)
        return scores

    def embed(self, keyword_lists, keyword_lengths):
        """
        :param keyword_lists: Numpy array - Batch_size by max_num_keywords - integers corresponding to keywords in the vocabulary.
        :param keyword_lengths: numpy array - batch_size by 1
        :return: batch_size by embedding dim
        """

        '''
        Keep this here for now.
        '''
        if False:
            pass
        # if self.cached_ft:
        #     print('Using fasttext pretrained embeddings')
        #     D = self.cached_ft.get_dimension()
        #     # Get the phrases
        #     summed_emb = np.zeros((keyword_lists.shape[0], D))
        #     for idx, author_kps in enumerate(keyword_lists):
        #         embeddings = np.zeros((len(author_kps), D))
        #         for phr_idx, phrase in enumerate(author_kps):
        #             if phrase:
        #                 embeddings[phr_idx, :] = self.cached_ft.get_word_vector(self.vocab.id2item[phrase])
        #             else:
        #                 embeddings[phr_idx, :] = np.zeros((D,))
        #         summed_emb[idx, :] = np.sum(embeddings, axis=0)
        #     averaged = summed_emb / keyword_lengths
        #     return torch.from_numpy(averaged)
        else:
            kw_indices = torch.from_numpy(keyword_lists).long()
            kw_lengths = torch.from_numpy(keyword_lengths)
            if self.config.use_cuda:
                kw_indices = kw_indices.cuda()
                kw_lengths = kw_lengths.cuda()
            # B by L by d
            embeddings = self.embedding(kw_indices)
            kw_lengths[kw_lengths == 0] = 1
            summed_emb = torch.sum(embeddings, dim=1)
            averaged = torch.div(summed_emb, kw_lengths.float())
            return averaged

    def embed_dev(self, keyword_lists, keyword_lengths, print_embed=False, batch_size=None):
        """
        :param keyword_lists: Batch_size by max_num_keywords
        :return: batch_size by embedding dim
        """
        return self.embed(keyword_lists, keyword_lengths)

    def score_dev_test_batch(self,
        batch_queries,
        batch_query_lengths,
        batch_targets,
        batch_target_lengths,
        batch_size
        ):

        if batch_size == self.config.dev_batch_size:
            source_embed = self.embed_dev(batch_queries, batch_query_lengths)
            target_embed = self.embed_dev(batch_targets, batch_target_lengths)
        else:
            source_embed = self.embed_dev(batch_queries, batch_query_lengths, batch_size=batch_size)
            target_embed = self.embed_dev(batch_targets, batch_target_lengths, batch_size=batch_size)

        scores = utils.row_wise_dot(source_embed, target_embed)

        # what is this?
        scores[scores != scores] = 0

        return scores


def generate_predictions(config, model, batcher):
    """
    Use the model to make predictions on the data in the batcher

    :param model: Model to use to score reviewer-paper pairs
    :param batcher: Batcher containing data to evaluate (a DevTestBatcher)
    :return:
    """

    for idx, batch in enumerate(batcher.batches(batch_size=config.dev_batch_size)):
        if idx % 100 == 0:
            print('Predicted {} batches'.format(idx))

        batch_queries = []
        batch_query_lengths = []
        batch_query_ids = []
        batch_targets = []
        batch_target_lengths = []
        batch_target_ids = []
        batch_labels = []
        batch_size = len(batch)

        for data in batch:
            # append a positive sample
            batch_queries.append(data['source'])
            batch_query_lengths.append(data['source_length'])
            batch_query_ids.append(data['source_id'])
            batch_targets.append(data['positive'])
            batch_target_lengths.append(data['positive_length'])
            batch_target_ids.append(data['positive_id'])
            batch_labels.append(1)

            # append a negative sample
            batch_queries.append(data['source'])
            batch_query_lengths.append(data['source_length'])
            batch_query_ids.append(data['source_id'])
            batch_targets.append(data['negative'])
            batch_target_lengths.append(data['negative_length'])
            batch_target_ids.append(data['negative_id'])
            batch_labels.append(0)

        scores = model.score_dev_test_batch(
            np.asarray(batch_queries),
            np.asarray(batch_query_lengths),
            np.asarray(batch_targets),
            np.asarray(batch_target_lengths),
            np.asarray(batch_size)
        )

        if type(batch_labels) is not list:
            batch_labels = batch_labels.tolist()

        if type(scores) is not list:
            scores = list(scores.cpu().data.numpy().squeeze())

        for source, source_id, target, target_id, label, score in zip(
            batch_queries,
            batch_query_ids,
            batch_targets,
            batch_target_ids,
            batch_labels,
            scores
            ):

            # temporarily commenting out "source" and "target" because I think they are not needed.
            prediction = {
                # 'source': source,
                'source_id': source_id,
                # 'target': target,
                'target_id': target_id,
                'label': label,
                'score': float(score)
            }

            yield prediction

def load_jsonl(filename):

    labels_by_forum = defaultdict(dict)
    scores_by_forum = defaultdict(dict)

    for data in utils.jsonl_reader(filename):
        forum = data['source_id']
        reviewer = data['target_id']
        label = data['label']
        score = data['score']
        labels_by_forum[forum][reviewer] = label
        scores_by_forum[forum][reviewer] = score


    result_labels = []
    result_scores = []

    for forum, labels_by_reviewer in labels_by_forum.items():
        scores_by_reviewer = scores_by_forum[forum]

        reviewer_scores = list(scores_by_reviewer.items())
        reviewer_labels = list(labels_by_reviewer.items())

        sorted_labels = [label for _, label in sorted(reviewer_labels)]
        sorted_scores = [score for _, score in sorted(reviewer_scores)]

        result_labels.append(sorted_labels)
        result_scores.append(sorted_scores)

    return result_labels, result_scores

def eval_map_file(filename):
    list_of_list_of_labels, list_of_list_of_scores = utils.load_labels(filename)
    return eval_map(list_of_list_of_labels, list_of_list_of_scores)

def eval_hits_at_k_file(filename, k=2, oracle=False):
    list_of_list_of_labels,list_of_list_of_scores = utils.load_labels(filename)
    return eval_hits_at_k(list_of_list_of_labels, list_of_list_of_scores, k=k,oracle=oracle)

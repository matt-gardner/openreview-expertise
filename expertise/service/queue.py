import hashlib, json, threading, queue
from multiprocessing import Queue
from typing import *
from dataclasses import dataclass, field

@dataclass
class JobData:
    """Keeps track of job information and status"""
    id: str = field(
        metadata={"help": "The profile id at the time of submission"},
    )
    job_name: str = field(
        metadata={"help": "The name of the job specified in the submitted config file"},
    )
    job_id: str = field(
        metadata={"help": "The unique id for this job"},
    )
    config: dict = field(
        metadata={"help": "The submitted configuration file as a dictionary"},
    )
    status: str = field(
        default='Queued',
        metadata={"help": "The current status of this job"},
    )
    timeout: int = field(
        default=0,
        metadata={"help": "The maximum amount of time to run this job"},
    )

    def __post_init__(self):
        # Generate job id
        config_string = json.dumps(self.config)
        self.job_id = hashlib.md5(config_string.encode('utf-8')).hexdigest()

    def to_json(self):
        """
        Converts JobData instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a JobData instance
        :rtype: dict
        """
        return {
            'id': self.id,
            'job_name': self.job_name,
            'job_id': self.job_id,
            'config': self.config,
            'status': self.status,
            'timeout': self.timeout
        }

class JobQueue:
    """
    Keeps track of queue metadata in-memory and is responsible for queuing jobs when given a config
    Important attributes:
        q -- The Python queue which from which the daemon thread pulls JobData objects
        submitted -- A list of JobData objects which have been submitted (to be updated to a redundant database like redis)
    """
    def __init__(self, max_size: int = 0) -> None:
        """
        Instantiates a JobQueue object using a max_size parameter which determines the amount of concurrent jobs that can be run which depends the type of computation
        and system resources. If no max_size is provided, default to infinity.

        :param max_size: Integer of the amount of concurrent jobs
        :type max_size: int
        """
        self.q = Queue(maxsize=max_size)
        self.submitted = list()
        self.lock_submitted = threading.Lock()
        pass
    
    def put_job(self, request: JobData) -> None:
        """
        Adds a JobData object to the queue to be processed asynchronously
        
        :param request: A JobData object containing the metadata of the job to be executed
        :type request: JobData
        """
        pass
    
    def cancel_job(self, user_id: str, job_id: str = '', job_name: str = '') -> str:
        """
        For a job that is still queued, sets the status to stale to ensure that it does not get processed
        Currently, cannot cancel a job that is already in processing
        Identify the job to be canceled with a combination of the user_id and the optional arguments
        If no job_id is provided, uses job_name
        if no job_name is provided, uses job_id

        :param user_id: A string containing the user id that has submitted jobs
        :type user_id: str

        :param job_id: A string containing the submitted job id
        :type job_id: str

        :param job_name: A string containing the user specified name for the job
        :type job_name: str
        """
        pass

    def get_jobs(self, user_id: str) -> list:
        """
        Returns a list of job names and ids of all jobs associated with the user id, and their statuses

        :param user_id: A string containing the user id that has submitted jobs
        :type user_id: str
        """
        pass

    def get_status(self, user_id: str, job_id: str = '', job_name: str = '') -> str:
        """
        Return the status of the job submitted by user_id with either the given job_id or job_name
        If no job_id is provided, uses job_name
        if no job_name is provided, uses job_id

        :param user_id: A string containing the user id that has submitted jobs
        :type user_id: str

        :param job_id: A string containing the submitted job id
        :type job_id: str

        :param job_name: A string containing the user specified name for the job
        :type job_name: str
        """
        pass

    def get_result(self, user_id: str, delete_on_get: bool = True, job_id: str = '', job_name: str = '') -> dict:
        """
        Return the result of the job submitted by user_id with either the given job_id or job_name
        If no job_id is provided, uses job_name
        if no job_name is provided, uses job_id
        By default, deletes the data and metadata with the associated job 

        :param user_id: A string containing the user id that has submitted jobs
        :type user_id: str

        :param delete_on_get: A boolean flag that decides whether or not to maintain the data and metadata from the job
        :type delete_on_get: bool

        :param job_id: A string containing the submitted job id
        :type job_id: str

        :param job_name: A string containing the user specified name for the job
        :type job_name: str
        """
        pass
    
    # ------------ PRIVATE FUNCTIONS ------------
    def _daemon(self) -> None:
        """Job queue daemon function that continuously attempts to consume from the queue"""
        pass
    
    @classmethod
    def _handle_job(job_info: JobData) -> None:
        """Creates a process to perform the job, sleeps and kills process on wake up if process is still alive"""
        pass

    @classmethod
    def _run_job(config: dict) -> None:
        """The actual work, set of functions to be run in a subprocess from the _handle_job thread"""
        pass

    def _get_job_data(self, user_id: str, job_id: str = '', job_name: str = '') -> list:
        """
        Fetches a list of JobData objects that have been submitted by user_id with either the given job_id or job_name
        If no job_id is provided, uses job_name
        if no job_name is provided, uses job_id

        :param user_id: A string containing the user id that has submitted jobs
        :type user_id: str

        :param job_id: A string containing the submitted job id
        :type job_id: str

        :param job_name: A string containing the user specified name for the job
        :type job_name: str
        """
        pass
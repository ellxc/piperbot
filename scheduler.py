import datetime

from threading import Thread, Event
from multiprocessing.pool import ThreadPool
from dateutil import parser


class Scheduler(Thread):
    def __init__(self, threads=4):
        super(Scheduler, self).__init__(daemon=True)
        self.Tasks = []
        self.event = Event()
        self.ticking = False
        self.worker_pool = ThreadPool(processes=threads)

    @property
    def idle_time(self):
        validtasks = list(filter(lambda task: not task.running, self.Tasks))
        if validtasks:
            return (min(validtasks).next_run - datetime.datetime.now()).total_seconds()
        return None

    def run(self):
        self.ticking = True
        while self.ticking:
            to_run = filter(lambda task: task.should_run and not task.running, self.Tasks)

            for task in to_run:
                task.running = True
                self.worker_pool.apply_async(task.run, callback=self.reschedule_or_cancel)

            self.event.wait(self.idle_time)
            self.event.clear()

    def add_task(self, task):
        if task.schedule():
            self.Tasks.append(task)
            self.event.set()
        return task

    def reschedule_or_cancel(self, task):
        if not task.schedule():
            self.cancel_task(task)
        else:
            task.running = False
            self.event.set()

    def clear(self):
        del self.Tasks[:]

    def cancel_task(self, job):
        try:
            self.Tasks.remove(job)
        except ValueError:
            pass


class Task():
    def __init__(self, interval=0, unit="seconds", start_time=None, start_date=None, max_runs=1, task=None,
                 straight_away=True):
        self.interval = interval
        self.unit = unit
        self.start_time = start_time
        self.start_date = start_date
        self.no_of_runs = 0
        self.max_runs = max_runs
        self.straight_away = straight_away
        self.next_run = None
        self.period = None
        self.task = task
        self.running = False

    def run(self):
        if self.task is not None:
            try:
                self.task()
            except Exception as e:
                print("*** Scheduled Task Failed to run: %s" % e)
        else:
            print("*** Scheduled Task had no Task specifed")
        self.no_of_runs += 1
        return self

    def do(self, task):
        self.task = task
        return self

    def at(self, strtime):
        self.start_time = parser.parse(strtime).time()
        self.straight_away = True
        return self

    def on(self, strdate):
        self.start_date = parser.parse(strdate).date()
        self.straight_away = True
        return self

    def times(self, no):
        self.max_runs = no
        return self

    def schedule(self):
        if self.no_of_runs == 0:
            self.period = datetime.timedelta(**{self.unit: self.interval})
            if self.start_date is None or self.start_date < datetime.datetime.now().date():
                self.start_date = datetime.datetime.now().date()
            if self.start_time is None or self.start_time < datetime.datetime.now().time():
                self.start_time = datetime.datetime.now().time()
            self.next_run = datetime.datetime.combine(self.start_date, self.start_time)
            if not self.straight_away:
                self.next_run += self.period
            return True
        elif self.no_of_runs < self.max_runs or self.max_runs == -1:
            self.next_run += self.period
            return True
        return False

    @classmethod
    def every(cls, interval=1):
        task = Task(interval, max_runs=-1, straight_away=False)
        return task

    @classmethod
    def once(cls, interval=0):
        task = Task(interval=interval, max_runs=1, straight_away=False)
        return task

    @property
    def second(self):
        return self.seconds

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minute(self):
        return self.minutes

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hour(self):
        return self.hours

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def day(self):
        return self.days

    @property
    def days(self):
        self.unit = 'days'
        return self

    @property
    def weeks(self):
        self.unit = 'weeks'
        return self

    @property
    def week(self):
        return self.weeks

    @property
    def monday(self):
        self.start_date = parser.parse('monday')
        return self.weeks

    @property
    def tuesday(self):
        self.start_date = parser.parse('tuesday')
        return self.weeks

    @property
    def wednesday(self):
        self.start_date = parser.parse('wednesday')
        return self.weeks

    @property
    def thursday(self):
        self.start_date = parser.parse('thursday')
        return self.weeks

    @property
    def friday(self):
        self.start_date = parser.parse('friday')
        return self.weeks

    @property
    def saturday(self):
        self.start_date = parser.parse('saturday')
        return self.weeks

    @property
    def sunday(self):
        self.start_date = parser.parse('sunday')
        return self.weeks

    @property
    def should_run(self):
        return datetime.datetime.now() >= self.next_run

    def __lt__(self, other):
        return self.next_run < other.next_run

    def __repr__(self):
        return str(self.next_run)
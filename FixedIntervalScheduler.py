"""
定时 定间隔，运行任务

主线程 - FixedIntervalScheduler，
    - run() 循环判断是否应该运行任务
        - 任务 - FixedIntervalTask
            - 新线程 运行任务 FixedIntervalTask.run_task()
                - subprocess.Popen(bat)
                - 如果报错，则 Exception， 但是不会影响其他线程运行，也不会影响此任务的其他执行
        -
# TODO 捕获错误 并暂停任务
"""

import os
import shutil
import sys
from time import sleep
from datetime import datetime, time, timedelta
import threading
from typing import List, Dict
from collections import defaultdict, namedtuple
import json
import subprocess

PATH_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PATH_ROOT)

from helper.simpleLogger import MyLogger
from helper.tp_WarningBoard import run_warning_board


class FixedIntervalTask:
    def __init__(
            self,
            name, running_bat, interval, running_time: List[List[datetime]],
            skip_holiday=False,
            logger=MyLogger('FixedIntervalTask'),
            *args, **kwargs
    ):
        assert os.path.isfile(running_bat)
        assert type(skip_holiday) is bool
        self.name = name
        self.interval = int(interval)
        self.running_time: List[List[time]] = [[_.time() for _ in _l] for _l in running_time]
        self.running_timing: List[time] = self._gen_running_timing(running_time)            # 运行时间点
        self.running_bat_path = running_bat
        self.skip_holiday = skip_holiday
        # 上一次运行的时间time
        self.last_running_timing: time = time(hour=0, minute=0, second=0)
        # 是否正在执行任务
        self.is_in_running = False
        # 运行编号
        self.running_task_id = '_'

        self.logger = logger
        print(str(self))

    def _gen_running_timing(self, running_time):
        l_running_timing: List[time] = []
        for a_time_range in running_time:
            _start: datetime = a_time_range[0]
            _end: datetime = a_time_range[1]
            _timing = _start
            while _timing <= _end:
                l_running_timing.append(_timing.time())
                _timing += timedelta(seconds=self.interval)
        l_running_timing.sort()
        return l_running_timing

    def __str__(self):
        return f"""
FixedIntervalTask[
    Name: {self.name},
    RunningBatch: {str(self.running_bat_path)},
    RunningTime: {str(self.running_time)},
    Interval: {str(self.interval)} s,
    SkipHoliday: {str(self.skip_holiday)},
]            
        """

    def is_running_timing(self, timing: time) -> bool:
        # 检查 输入的时间点，是否应该运行任务
        # 小于上一次执行任务的时间
        if len(self.running_time) == 0:
            return False
        # 检查离输入时间点最近的 且小于输入时间点的 应该执行任务的时间点
        target_n = None
        for n, a_running_timing in enumerate(self.running_timing):
            if timing < a_running_timing:
                target_n = n - 1
                break
            else:
                target_n = n
        if target_n is None:
            # target_n is None
            return False
        if target_n == -1:
            # timing < self.running_timing[0]
            return False
        _nearly_running_timing_small = self.running_timing[target_n]
        # print(timing, self.last_running_timing, _nearly_running_timing_small)
        # 对比
        if _nearly_running_timing_small <= self.last_running_timing:
            return False
        else:
            # self.last_running_timing = timing
            return True

    def run_task(self, timing):
        def _run() -> bool:
            p = subprocess.Popen(
                #     # args
                #     # 最好传递一个sequence，因为它允许模块处理任何必需的参数转义和引用;
                #     # 如果传递的是字符串，则shell必须为True; 否则该字符串必须简单地为要执行的程序的名字，而不能指定任何参数。
                # 'main.py',
                # self.running_bat_path,
                f"{self.running_bat_path}",
                # f'call "{self.running_bat_path}"',
                cwd=os.path.dirname(self.running_bat_path),
                # stdout=subprocess.PIPE,
                # shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            try:
                outs, errs = p.communicate()
                # self.logger.info('communicated')
                if outs:
                    outs = outs.decode()
                else:
                    outs = ''
                if errs:
                    errs = errs.decode()
                else:
                    errs = ''
            except subprocess.TimeoutExpired as e:
                self.logger.error(e)
                return False
            except Exception as e:
                self.logger.error(e)
                return False
            else:
                if errs:
                    self.logger.error(errs)
                    return False
                elif 'exception' in outs.lower():
                    self.logger.error(outs)
                    return False
                else:
                    return True
            finally:
                p.kill()

        #
        self.is_in_running = True
        self.last_running_timing = timing
        self._update_running_task_id()
        self.logger.info(f'running task, {self.name}, {self.running_task_id}')
        _success = _run()
        if _success:
            self.logger.info(f'finished task, {self.name}, {self.running_task_id}')
            self.is_in_running = False
        else:
            self.logger.error(f'something wrong in task, {self.name}, {self.running_task_id}')
            self.is_in_running = False
            raise Exception

    def _update_running_task_id(self):
        _last_id_date = self.running_task_id.split('_')[0]
        _last_id_num = self.running_task_id.split('_')[-1]
        if _last_id_num == '':
            _last_id_num = 0
        else:
            _last_id_num = float(_last_id_num)
        _new_date = datetime.now().strftime('%Y%m%d')
        if _new_date != _last_id_date:
            _new_num = 1
        else:
            _new_num = _last_id_num + 1
        self.running_task_id = f'{_new_date}_{str(int(_new_num))}'
        return self.running_task_id

    @property
    def running_num(self) -> int:
        _num = self.running_task_id.split('_')[1]
        if _num == "":
            return 0
        else:
            return int(_num)


class FixedIntervalScheduler:
    """
    配置样式：
        ./TASK_1                    # 纯粹是文件夹名字 不提供任何信息
            ./config.json               # 配置，包括：任务名称、运行时间段、运行的间隔时间。文件名字固定
            。/start.bat            # 按照配置，在指定时间点，调用此bat。文件名字固定
        ./TASK_2

    在启动时，扫描一次，并记录任务文件夹的路径和任务的配置；之后不再扫描；
    **对任务配置作任何修改后，都需要重启；**
        新增任务文件夹，需要重启
        修改任务的配置，需要重启
        删除任务文件夹，报错并终止，需要重启
        修改任务文件夹名称，报错并终止，需要重启
        文件缺失，报错并终止

    所有任务，使用同一个，全局的时钟管理、任务分配器


    """
    def __init__(self, path_task_config_folder, logger=MyLogger('FixedIntervalScheduler')):
        self.p_task_config_folder = os.path.abspath(path_task_config_folder)
        # 任务实例
        self.l_scheduler_tasks: List[FixedIntervalTask] = self._create_tasks()

        self.logger = logger

    def _create_tasks(self) -> List[FixedIntervalTask]:
        """
        初始化时，读取任务配置，创建任务实例
        """
        def _check_task_config(_d: dict) -> dict or None:
            _d = _d.copy()
            _d_new = {}
            _error = False
            # 1
            if "name" not in _d.keys():
                self.logger.error("配置文件缺少关键字, ’name‘")
                _error = True
            else:
                _d_new["name"] = _d["name"]
            # 2
            if "interval" not in _d.keys():
                _error = True
            else:
                try:
                    _d_new["interval"] = int(_d["interval"])
                except:
                    self.logger.error("配置文件错误, ’interval‘")
                    _error = True
            # 3
            if "running_time" not in _d.keys():
                _d_new["running_time"] = [[
                    datetime.strptime("0:00:00", "%H:%M:%S"), datetime.strptime("23:59:59", "%H:%M:%S")]]
            else:
                try:
                    _d_new["running_time"] = []
                    for _l in _d["running_time"]:
                        _s = datetime.strptime(_l[0], "%H:%M:%S")
                        _e = datetime.strptime(_l[1], "%H:%M:%S")
                        if _s >= _e:
                            self.logger.error("配置文件错误, ’running_time‘")
                            _error = True
                        else:
                            _d_new["running_time"].append([_s, _e])
                except :
                    self.logger.error("配置文件错误, ’running_time‘")
                    _error = True
            # 4
            if "skip_holiday" not in _d.keys():
                pass
            else:
                try:
                    _d_new["skip_holiday"] = bool(_d["skip_holiday"])
                except :
                    self.logger.error("配置文件错误, ’skip_holiday‘")
                    _error = True
            # return
            if _error:
                return None
            else:
                return _d_new

        l_tasks: List[FixedIntervalTask] = []
        # 读取任务配置
        assert os.path.isdir(self.p_task_config_folder)
        for task_folder_name in os.listdir(self.p_task_config_folder):
            p_task_folder = os.path.join(self.p_task_config_folder, task_folder_name)
            if not os.path.isdir(p_task_folder):
                continue
            p_task_config = os.path.join(p_task_folder, 'config.json')
            p_task_bat = os.path.join(p_task_folder, 'start.bat')
            if not os.path.isfile(p_task_config):
                self.logger.error('找不到任务配置文件, %s' % p_task_config)
                raise FileNotFoundError
            if not os.path.isfile(p_task_bat):
                self.logger.error('找不到任务bat文件, %s' % p_task_bat)
                raise FileNotFoundError
            # 读取配置
            with open(p_task_config) as f:
                d_config: dict = json.load(f)
                # print(d_config)
            d_config = _check_task_config(d_config)
            if not d_config:
                self.logger.error(f"reading {p_task_config}")
                raise ValueError
            l_tasks.append(
                FixedIntervalTask(
                    running_bat=p_task_bat,
                    **d_config
                )
            )
        if len(l_tasks) == 0:
            self.logger.error('未发现任务配置')
            raise Exception
        return l_tasks

    def run(self):
        while True:
            _now = datetime.now()
            _date = _now.date()
            _time = _now.time()
            _is_weekend = _now.weekday() >= 5
            for _task in self.l_scheduler_tasks:
                # 是否周末
                if _is_weekend:
                    if _task.skip_holiday:
                        continue
                if _task.is_running_timing(_time):
                    if _task.is_in_running:
                        continue
                    else:
                        _threading = threading.Thread(
                            target=_task.run_task,
                            args=[_time]
                        )
                        _threading.start()
            # 间隔1s，避免性能占用
            sleep(1)


def t():
    scheduler = FixedIntervalScheduler(
        os.path.join(PATH_ROOT, "Config/TaskList"),
        logger=MyLogger('Scheduler', output_root=os.path.join(PATH_ROOT, 'logs'))
    )
    scheduler.run()


if __name__ == '__main__':
    t()

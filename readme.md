# FixedIntervalScheduler

在日内固定时间区间,按固定时间间隔运行的定时任务器。

## 运行

### 配置文件

- 固定的配置目录, "./Config/TaskList/"
- 每个任务一个文件夹,任意文件夹名
- 任务文件夹下必须有两个文件: Config.json, start.bat
- Config.json 如下,必须包含以下所有配置项
```json
{
  "name": "test_1",
  "running_time": [
    ["9:00:00", "15:00:00"],
    ["16:00:00", "23:00:00"]
  ],
  "interval": 5,
  "skip_holiday": false
}
```
- start.bat 是任务所调用的文件, eg:
```bat
chcp 65001
@echo off

cd %~dp0
python main.py

exit
```

### 启动程序
./_run.bat 启动任务器。

## 说明

### 配置项

- name: 任务名称,在log中显示
- running_time: 日内运行的时间区间, 格式参考上述内容
- interval: 运行的间隔时间, 单位为 秒
- skip_holiday: 是否跳过周末, bool值

### 程序运行

1. 读取配置, 将每个任务 实例化为 FixedIntervalTask对象. 初始化时根据 running_time 和 interval, 计算出运行的时间点 running_timing 
2. 初始化 任务器 FixedIntervalScheduler对象, 负责调用 FixedIntervalTask对象
3. FixedIntervalScheduler对象 每间隔1秒, 通过调用 FixedIntervalTask对象的检查方法, 判断当前时间点是否 需要执行任务
4. 若任务需要执行,启动新线程运行,并将 FixedIntervalTask对象的状态设置为 is_in_running=True,在此次任务结束前,不会重复运行该任务
5. 如果任务运行失败,报错并尝试重新运行,不阻塞


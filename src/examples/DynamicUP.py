from langup.listener.schema import SchedulingEvent
from langup import DynamicUP


DynamicUP(
    schedulers=[
        SchedulingEvent(input='请感谢大家的关注！', time='10m'),
        SchedulingEvent(input='请感谢大家的关注！', time='0:36')
    ]
).run()
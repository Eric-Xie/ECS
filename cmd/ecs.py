from multiprocessing import Process
from energy_saving import manager


def main():
    ecs_manager = manager.EcsManager()
    p = Process(target=ecs_manager.start, name='ecs')
    p.start()

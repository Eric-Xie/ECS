1. overview
ECS(Energy Consumption Saving) aims to save energy-consumption for openstack cloud. In one cloud, there may be thousands of hosts. But some hosts may be have no workload at some times. For energy saving, ECS can power off the hosts.


2. implements
1) run as service;
2) two policies:
    -> simple: power off hosts if hosts power-oning without vms larger than reservation.
               or else power on hosts.
    -> ratio: power off hosts if hosts power-oning with vms * percent larget than hosts power
               -oning without vms. or else power on hosts.


3. Change log
-----------------------------------
updated at 2015-7-24
* run as services
* add unit test cases
* change source architecture


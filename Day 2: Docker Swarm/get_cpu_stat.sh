#!/bin/bash

# Get initial CPU usage
cpu_usage_1=$(grep 'usage_usec' /sys/fs/cgroup/cpu.stat | awk '{print $2}')
# Wait for 1 second
sleep 1
# Get updated CPU usage
cpu_usage_2=$(grep 'usage_usec' /sys/fs/cgroup/cpu.stat | awk '{print $2}')
# Calculate CPU utilization in percentage
cpu_utilization=$(( (cpu_usage_2 - cpu_usage_1) / 10000 )) 
echo "CPU utilization: $cpu_utilization%"

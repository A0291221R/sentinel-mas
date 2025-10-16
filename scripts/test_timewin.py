
from sentinel_mas.timewin import resolve_time_window


# print(resolve_time_window("Who entered loc-iss-exit-1 on 13-oct-2025 time between 15:30–18:40 SGT?"))
# print(resolve_time_window("Who entered loc-iss-exit-1 on 13/oct/2025 time between 15:02–18:10 SGT?"))
# print(resolve_time_window("Who entered loc-iss-exit-1 on 13/10/2025 time between 15:45–18:57 SGT?"))
# # print(resolve_time_window("Who entered loc-iss-exit-1 on 13-10-2025 15:00-18:00?"))
# print(resolve_time_window("Who entered loc-iss-exit-1 on 13-10-2025 15:01-18:23?"))

# # today / yesterday / tomorrow with range
# print('\n today / yesterday / tomorrow with range')
# print(resolve_time_window("today 2pm–4:30pm"))
# print(resolve_time_window("yesterday 10am–11am"))
# print(resolve_time_window("tomorrow 09:00–11:00 lobby"))

# # durations
# print('\n durations')
# print(resolve_time_window("last 15 minutes"))
# print(resolve_time_window("last 2 hours"))

# # dayparts
# print('\n dayparts')
# print(resolve_time_window("this morning"))
# print(resolve_time_window("yesterday evening"))
# print(resolve_time_window("tonight"))

# # 'now' mixed
# print('\n now mixed')
# print(resolve_time_window("now–4pm"))
# print(resolve_time_window("2pm–now"))


# print(resolve_time_window('How many people visited loc-iss-exit-1 on 13-Oct-2025? Give total and unique visitors.'))
# print(resolve_time_window('List anomaly events for loc-iss-exit-1 on 2025-10-16 08:00–10:00, CAM-07, top 20.'))
# print(resolve_time_window("Show entries for Location=loc-iss-exit-1 from 10:15–11:00 SGT; include resolved_id if known."))
# print(resolve_time_window("List anomaly episodes with incident='anomaly' in loc-iss-exit-1 from 08:00–09:30 with confidence."))
# print(resolve_time_window("How many unique visitors at loc-iss-exit-1 during lunch 12:00–14:00?"))
# print(resolve_time_window("List anomaly episodes with incident='anomaly' in loc-iss-exit-1 from 08:00–09:30 with confidence."))
# print(resolve_time_window("Who entered loc-iss-exit-1 between 18:00–19:00, filtered to CAM-P03?"))
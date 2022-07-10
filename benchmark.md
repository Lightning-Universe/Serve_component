### DIRECT /predict

```bash
(.venv) ➜  lightning-serve git:(add_more) ✗ ab -n 10000 -c 1 -p payload.json -T "application/json" http://127.0.0.1:8000/predict
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        uvicorn
Server Hostname:        127.0.0.1
Server Port:            8000

Document Path:          /predict
Document Length:        17 bytes

Concurrency Level:      1
Time taken for tests:   25.902 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1420000 bytes
Total body sent:        5190000
HTML transferred:       170000 bytes
Requests per second:    386.07 [#/sec] (mean)
Time per request:       2.590 [ms] (mean)
Time per request:       2.590 [ms] (mean, across all concurrent requests)
Transfer rate:          53.54 [Kbytes/sec] received
                        195.67 kb/s sent
                        249.21 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       5
Processing:     1    2   1.6      2      79
Waiting:        1    2   1.5      2      79
Total:          2    3   1.6      2      80

Percentage of the requests served within a certain time (ms)
  50%      2
  66%      2
  75%      3
  80%      3
  90%      3
  95%      4
  98%      5
  99%      7
 100%     80 (longest request)
```

### GoGin Go-coro

```bash
(.venv) ➜  lightning-serve git:(add_more) ✗ ab -n 10000 -c 1 -p payload.json -T "application/json" http://127.0.0.1:60998/predict
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:
Server Hostname:        127.0.0.1
Server Port:            60998

Document Path:          /predict
Document Length:        21 bytes

Concurrency Level:      1
Time taken for tests:   35.549 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1440000 bytes
Total body sent:        5200000
HTML transferred:       210000 bytes
Requests per second:    281.30 [#/sec] (mean)
Time per request:       3.555 [ms] (mean)
Time per request:       3.555 [ms] (mean, across all concurrent requests)
Transfer rate:          39.56 [Kbytes/sec] received
                        142.85 kb/s sent
                        182.41 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       7
Processing:     2    3   3.0      3      93
Waiting:        2    3   2.9      3      93
Total:          2    4   3.0      3      93

Percentage of the requests served within a certain time (ms)
  50%      3
  66%      3
  75%      3
  80%      4
  90%      5
  95%      6
  98%     11
  99%     16
 100%     93 (longest request)
```

### GoGin No Go-coro

```bash
(.venv) ➜  lightning-serve git:(add_more) ✗ ab -n 10000 -c 1 -p payload.json -T "application/json" http://127.0.0.1:56056/predict
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:
Server Hostname:        127.0.0.1
Server Port:            56056

Document Path:          /predict
Document Length:        21 bytes

Concurrency Level:      1
Time taken for tests:   39.960 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1440000 bytes
Total body sent:        5200000
HTML transferred:       210000 bytes
Requests per second:    250.25 [#/sec] (mean)
Time per request:       3.996 [ms] (mean)
Time per request:       3.996 [ms] (mean, across all concurrent requests)
Transfer rate:          35.19 [Kbytes/sec] received
                        127.08 kb/s sent
                        162.27 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.6      0      55
Processing:     2    4   3.5      3      95
Waiting:        2    4   3.5      3      95
Total:          2    4   3.6      3      96

Percentage of the requests served within a certain time (ms)
  50%      3
  66%      4
  75%      4
  80%      4
  90%      5
  95%      7
  98%     13
  99%     19
 100%     96 (longest request)
```

### FastAPI workers=4

```bash
(.venv) ➜  lightning-serve git:(add_more) ✗ ab -n 10000 -c 1 -p payload.json -T "application/json" http://127.0.0.1:64192/predict
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        uvicorn
Server Hostname:        127.0.0.1
Server Port:            64192

Document Path:          /predict
Document Length:        17 bytes

Concurrency Level:      1
Time taken for tests:   50.388 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1420000 bytes
Total body sent:        5200000
HTML transferred:       170000 bytes
Requests per second:    198.46 [#/sec] (mean)
Time per request:       5.039 [ms] (mean)
Time per request:       5.039 [ms] (mean, across all concurrent requests)
Transfer rate:          27.52 [Kbytes/sec] received
                        100.78 kb/s sent
                        128.30 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       7
Processing:     3    5   3.5      4     155
Waiting:        3    5   3.5      4     155
Total:          3    5   3.5      5     156

Percentage of the requests served within a certain time (ms)
  50%      5
  66%      5
  75%      5
  80%      6
  90%      6
  95%      8
  98%     10
  99%     11
 100%    156 (longest request)
```

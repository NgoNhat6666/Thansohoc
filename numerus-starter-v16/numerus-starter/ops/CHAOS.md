# Chaos & Load Test Notes
- Use `k6 run ops/k6-loadtest.js` with env BASE_URL, API_KEY.
- Consider `pumba` or `chaos-mesh` to inject latency/packet loss on Kubernetes.
- Game days: simulate Redis down (disable REDIS_URL), spike traffic (2x VUs), slow disk (PVC throttling).

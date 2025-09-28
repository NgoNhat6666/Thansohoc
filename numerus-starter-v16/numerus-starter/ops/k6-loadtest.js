import http from 'k6/http';
import { sleep, check } from 'k6';
export let options = {
  vus: 20,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    checks: ['rate>0.99'],
  },
};
export default function () {
  const url = __ENV.BASE_URL + '/v1/analyze';
  const payload = JSON.stringify({
    full_name: 'Tran Thi B',
    date_of_birth: '1992-05-10',
    system: 'vietnamese_latin',
    detailed: true,
    locale: 'vi'
  });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': __ENV.API_KEY || 'default:demo_key_456'
    },
  };
  const res = http.post(url, payload, params);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}

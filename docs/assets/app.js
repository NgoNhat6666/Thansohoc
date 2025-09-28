function sumDigits(n){let s=0;for(const ch of String(n))if(/\d/.test(ch))s+=Number(ch);return s}
function reduceNumber(n){const m=new Set([11,22,33]);while(n>9&&!m.has(n))n=sumDigits(n);return n}
const alphaMap={};(()=>{const a='ABCDEFGHIJKLMNOPQRSTUVWXYZ';let v=1;for(const ch of a){alphaMap[ch]=v;v=v===9?1:v+1}})();
function lettersOnly(s){return s.normalize('NFD').replace(/\p{Diacritic}/gu,'').replace(/[^A-Za-z]/g,'')}
function vowelsOnly(s){return s.replace(/[^AEIOUY]/gi,'')}
function consonantsOnly(s){return s.replace(/[AEIOUY]/gi,'')}
function pythagoreanValue(s){let total=0;for(const ch of lettersOnly(s).toUpperCase())total+=alphaMap[ch]||0;return total}
function calc(name,dob){const birth=dob.replace(/-/g,'');const lifePath=reduceNumber(sumDigits(birth));const expression=reduceNumber(pythagoreanValue(name));const soulUrge=reduceNumber(pythagoreanValue(vowelsOnly(name)));const personality=reduceNumber(pythagoreanValue(consonantsOnly(name)));return{lifePath,expression,soulUrge,personality}}

function card(key,val){const labels={lifePath:'Life Path',expression:'Expression',soulUrge:'Soul Urge',personality:'Personality'};return `<div class="cardlet"><h4>${labels[key]}: <strong>${val}</strong></h4><p>${explain(key,val)}</p></div>`}
function explain(key,val){const generic={'1':'Lãnh đạo, chủ động.','2':'Hòa hợp, trực giác.','3':'Sáng tạo, giao tiếp.','4':'Kỷ luật, nền tảng.','5':'Tự do, thay đổi.','6':'Trách nhiệm, gia đình.','7':'Chiêm nghiệm, phân tích.','8':'Tham vọng, thành tựu.','9':'Nhân ái, phục vụ.','11':'Trực giác cao.','22':'Kiến trúc sư bậc thầy.','33':'Từ bi bậc thầy.'};return generic[String(val)]||''}

const form=document.getElementById('form');
const result=document.getElementById('result');
const cards=document.getElementById('cards');
form.addEventListener('submit',e=>{e.preventDefault();const name=document.getElementById('fullName').value.trim();const dob=document.getElementById('dob').value;const r=calc(name,dob);cards.innerHTML=['lifePath','expression','soulUrge','personality'].map(k=>card(k,r[k])).join('');result.classList.remove('hidden')});

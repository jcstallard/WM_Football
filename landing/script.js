// Simple slideshow script: cycles through slides every 5 seconds, with manual prev/next
document.addEventListener('DOMContentLoaded', function(){
  const slides = Array.from(document.querySelectorAll('.slide'));
  const prevBtn = document.getElementById('prev');
  const nextBtn = document.getElementById('next');
  let current = 0;
  const delay = 5000; // ms
  let timer = null;

  function show(index){
    slides.forEach((s,i)=> s.classList.toggle('active', i===index));
    current = index;
  }

  function next(){ show((current+1)%slides.length); }
  function prev(){ show((current-1+slides.length)%slides.length); }

  nextBtn.addEventListener('click', ()=>{ resetTimer(); next(); });
  prevBtn.addEventListener('click', ()=>{ resetTimer(); prev(); });

  function startTimer(){ timer = setInterval(next, delay); }
  function resetTimer(){ if(timer) clearInterval(timer); startTimer(); }

  // Preload images
  slides.forEach(s=>{ const img = new Image(); img.src = s.src; });

  show(0);
  startTimer();
});

// Start Dash via POST then open the dashboard URL
function startDashAndOpen(url){
  // ask local server to start dash and wait until it is responsive
  fetch('/start_dash', { method: 'POST' })
    .then(resp => resp.json().catch(()=>({})))
    .then(info => {
      // If server says dash is ready, navigate immediately
      if(info && info.ready){
        window.location.href = url; return;
      }
      // Otherwise poll the dashboard URL until it responds or timeout
      const start = Date.now();
      const timeout = 20000; // ms
      const interval = 500; // ms
      const tryFetch = ()=>{
        fetch(url, { method: 'HEAD' }).then(r=>{
          if(r.ok){ window.location.href = url; return; }
          if(Date.now() - start > timeout){ window.location.href = url; return; }
          setTimeout(tryFetch, interval);
        }).catch(()=>{
          if(Date.now() - start > timeout){ window.location.href = url; return; }
          setTimeout(tryFetch, interval);
        });
      };
      setTimeout(tryFetch, 400);
    })
    .catch(()=>{ window.location.href = url; });
}

document.addEventListener('click', function(e){
  const target = e.target;
  if(target.matches('#richmond')){
    e.preventDefault();
    startDashAndOpen('http://localhost:8051/richmond');
  }
  if(target.matches('#wm')){
    e.preventDefault();
    startDashAndOpen('http://localhost:8051/wm');
  }
});

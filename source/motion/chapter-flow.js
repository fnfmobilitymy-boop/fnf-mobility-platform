/* Reference-inspired camera and chapter transitions. Existing Kenny clips remain intact.
 * Tunable motion values; no video seeking, scroll hijack, or new rendering library.
 */
const KENNY_REFERENCE_MOTION={
  scrollLerp:.09,wheelMultiplier:.9,enterY:68,mobileEnterY:34,exitY:44,
  enterOpacity:.18,exitOpacity:.34,scrub:.4,
  cameraPeak:1.26,mobileCameraPeak:1.10,heroScrollScale:1.08,
  chapterRadius:30,mobileChapterRadius:20,
  cameraKeys:[0,2,4,6.2,7.8,10.05]
};
function kennyAttachReferenceCamera(root,isPaused){
  const video=root.querySelector('.kenny-hero-source'),screen=root.querySelector('.kenny-hero-screen');
  if(!video||!screen)return()=>{};
  const mobile=matchMedia('(max-width:760px)');let frame=null,raf=null,dead=false,visible=true;
  const ease=t=>t*t*(3-2*t);
  const sample=time=>{
    if(dead||!visible||document.hidden||isPaused())return;
    const peak=mobile.matches?KENNY_REFERENCE_MOTION.mobileCameraPeak:KENNY_REFERENCE_MOTION.cameraPeak;
    const keys=KENNY_REFERENCE_MOTION.cameraKeys,values=[1,1,1.025,peak,peak,1];
    let scale=1;
    for(let i=0;i<keys.length-1;i++)if(time>=keys[i]&&time<=keys[i+1]){
      const p=ease(Math.max(0,Math.min(1,(time-keys[i])/(keys[i+1]-keys[i]))));
      scale=values[i]+(values[i+1]-values[i])*p;break;
    }
    screen.style.setProperty('--reference-camera-scale',scale.toFixed(4));
    screen.dataset.cameraScale=scale.toFixed(4);
  };
  const stop=()=>{if(frame!==null)video.cancelVideoFrameCallback?.(frame);if(raf!==null)cancelAnimationFrame(raf);frame=raf=null};
  const queue=()=>{
    if(dead||!visible||document.hidden||isPaused()||video.paused||video.ended||frame!==null||raf!==null)return;
    if(video.requestVideoFrameCallback)frame=video.requestVideoFrameCallback((_,meta)=>{frame=null;sample(meta.mediaTime);queue()});
    else raf=requestAnimationFrame(()=>{raf=null;sample(video.currentTime);queue()});
  };
  const play=()=>{sample(video.currentTime);queue()};
  const reset=()=>{stop();screen.style.setProperty('--reference-camera-scale','1');screen.dataset.cameraScale='1'};
  const visibility=()=>{if(document.hidden)stop();else play()};
  const observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;visible?play():stop()},{threshold:0});observer.observe(root.querySelector('#home'));
  video.addEventListener('play',play);video.addEventListener('pause',stop);video.addEventListener('ended',reset);
  video.addEventListener('loadeddata',play);document.addEventListener('visibilitychange',visibility);mobile.addEventListener?.('change',play);play();
  return()=>{dead=true;stop();observer.disconnect();video.removeEventListener('play',play);video.removeEventListener('pause',stop);video.removeEventListener('ended',reset);video.removeEventListener('loadeddata',play);document.removeEventListener('visibilitychange',visibility);mobile.removeEventListener?.('change',play);screen.style.removeProperty('--reference-camera-scale');delete screen.dataset.cameraScale};
}
function ol(e,t,n){
  const scrollRef=y.useRef(null),paused=y.useRef(n);paused.current=n;
  y.useLayoutEffect(()=>{
    const root=e.current;if(!root||t)return;
    root.classList.add('reference-motion-enabled','chapter-stack-enabled');
    const settings=KENNY_REFERENCE_MOTION;
    const lenis=new il({lerp:settings.scrollLerp,wheelMultiplier:settings.wheelMultiplier,smoothWheel:true,syncTouch:false,allowNestedScroll:true,prevent:node=>!!node.closest('dialog, [data-lenis-prevent]')});
    scrollRef.current=lenis;if(paused.current)lenis.stop();
    const update=()=>{X.update();const interactive=['coverage','project-brief'].some(id=>{const section=root.querySelector('#'+id);if(!section)return false;const bounds=section.getBoundingClientRect();return bounds.top<innerHeight*.8&&bounds.bottom>innerHeight*.2});root.classList.toggle('chapter-interaction-active',interactive)},tick=time=>lenis.raf(time*1000);lenis.on('scroll',update);Ii.ticker.add(tick);Ii.ticker.lagSmoothing(0);
    const narrow=matchMedia('(max-width:760px)');
    const sections=Array.from(root.querySelectorAll('main > .chapter-shell > section[id],main > section[id]'));
    const measureChapters=()=>{const viewport=innerHeight;root.style.setProperty('--chapter-viewport',viewport+'px');sections.forEach((section,index)=>{section.style.setProperty('--chapter-top',Math.min(0,viewport-section.offsetHeight)+'px');const shell=section.closest('.chapter-shell');shell?.style.setProperty('--chapter-layer',String(index+1));shell?.style.setProperty('--chapter-height',section.offsetHeight+'px')})};measureChapters();
    const ctx=Ii.context(()=>{
      sections.forEach((section,index)=>{
        section.dataset.chapterFlow='reference';
        const anchor=section.closest('.chapter-shell')||section;
        const copy=Array.from(section.querySelectorAll(al));
        const interactive=section.id==='coverage'||section.id==='project-brief';
        if(index>0&&!interactive)Ii.fromTo(section,{'--chapter-radius':()=> (narrow.matches?settings.mobileChapterRadius:settings.chapterRadius)+'px'},{'--chapter-radius':'0px',ease:'none',scrollTrigger:{trigger:anchor,start:'top 98%',end:'top 8%',scrub:.35,invalidateOnRefresh:true}});
        if(index>0&&!interactive&&copy.length)Ii.fromTo(copy,{y:()=>narrow.matches?settings.mobileEnterY:settings.enterY,opacity:settings.enterOpacity},{y:0,opacity:1,ease:'none',immediateRender:false,scrollTrigger:{trigger:anchor,start:'top 92%',end:'top 28%',scrub:settings.scrub,invalidateOnRefresh:true}});
        // Keep outgoing copy readable while the next chapter covers it.
        const backdrop=section.querySelector(':scope > .scene-backdrop, :scope > .hero-media, :scope > .index-room');
        if(backdrop)Ii.fromTo(backdrop,{y:0},{y:()=>Math.min(innerHeight*.075,70),ease:'none',immediateRender:false,scrollTrigger:{trigger:anchor,start:'top top',end:'bottom top',scrub:settings.scrub,invalidateOnRefresh:true}});
        const scene=section.querySelectorAll('.scene-original,.scene-first-frame,.scene-character-idle');
        if(scene.length)Ii.fromTo(scene,{scale:()=>narrow.matches?1.035:1.10},{scale:1,transformOrigin:'75% 45%',ease:'none',immediateRender:false,scrollTrigger:{trigger:anchor,start:'top bottom',end:'top top',scrub:.5,invalidateOnRefresh:true}});
      });
      const home=root.querySelector('#home'),player=root.querySelector('.kenny-hero-player');
      if(home&&player)Ii.to(player,{scale:()=>narrow.matches?1.025:settings.heroScrollScale,transformOrigin:'78% 42%',ease:'none',scrollTrigger:{trigger:home,start:'top top',end:'bottom top',scrub:.45,invalidateOnRefresh:true}});
      const cassette=root.querySelector('#index .cassette-stage');
      if(cassette)Ii.fromTo(cassette,{scale:.72,rotationX:12,rotationY:-10},{scale:1,rotationX:0,rotationY:0,ease:'none',immediateRender:false,scrollTrigger:{trigger:'#index',start:'top 90%',end:'top 20%',scrub:.5,invalidateOnRefresh:true}});
      const gallery=root.querySelector('#projects .work-gallery');
      if(gallery)Ii.fromTo(gallery,{scale:.93},{scale:1,ease:'none',immediateRender:false,scrollTrigger:{trigger:'#projects',start:'top 92%',end:'top 22%',scrub:.4,invalidateOnRefresh:true}});
      root.querySelectorAll('#timeline .journey-list > *').forEach((row,index)=>Ii.fromTo(row,{x:()=>narrow.matches?16:(index%2?32:-32),opacity:.28},{x:0,opacity:1,ease:'none',immediateRender:false,scrollTrigger:{trigger:row,start:'top 94%',end:'top 70%',scrub:.3,invalidateOnRefresh:true}}));
    },root);
    const detachCamera=kennyAttachReferenceCamera(root,()=>paused.current);
    let alive=true,resizeFrame=0;
    const refresh=()=>{measureChapters();lenis.resize();X.refresh()};
    document.fonts.ready.then(()=>{if(alive)refresh()});window.addEventListener('load',refresh,{once:true});window.addEventListener('resize',refresh);
    const observer=new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(refresh)}),main=root.querySelector('main');if(main)observer.observe(main);sections.forEach(section=>observer.observe(section));
    return()=>{alive=false;observer.disconnect();cancelAnimationFrame(resizeFrame);window.removeEventListener('load',refresh);window.removeEventListener('resize',refresh);detachCamera();ctx.revert();root.classList.remove('reference-motion-enabled','chapter-stack-enabled','chapter-interaction-active');root.style.removeProperty('--chapter-viewport');sections.forEach(section=>{section.style.removeProperty('--chapter-top');section.style.removeProperty('--chapter-radius');section.closest('.chapter-shell')?.style.removeProperty('--chapter-layer');section.closest('.chapter-shell')?.style.removeProperty('--chapter-height')});root.querySelectorAll('[data-chapter-flow]').forEach(node=>node.removeAttribute('data-chapter-flow'));lenis.off('scroll',update);Ii.ticker.remove(tick);lenis.destroy();Ii.ticker.lagSmoothing(500,33);if(scrollRef.current===lenis)scrollRef.current=null};
  },[e,t]);
  y.useEffect(()=>{n?scrollRef.current?.stop():scrollRef.current?.start()},[n]);
  return y.useCallback(id=>{const target=document.getElementById(id);if(!target)return;const lenis=scrollRef.current;if(!lenis||t)target.scrollIntoView({behavior:'instant',block:'start'});else lenis.scrollTo(target.closest('.chapter-shell')||target,{duration:Math.min(1.35,Math.max(.65,Math.abs(target.getBoundingClientRect().top)/2200)),easing:value=>1-(1-value)**3,force:true,onComplete:()=>X.update()})},[t]);
}

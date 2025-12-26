import React, { useState, useEffect, useRef } from 'react';
import Globe from 'react-globe.gl';

function App() {
  const [arcsData, setArcsData] = useState([]);
  const [logs, setLogs] = useState([]);
  const globeEl = useRef();

  useEffect(() => {
    // Auto-rotate globe for a cinematic feel
    if (globeEl.current) {
      globeEl.current.controls().autoRotate = true;
      globeEl.current.controls().autoRotateSpeed = 0.5;
    }

    const socket = new WebSocket('ws://localhost:8000/ws');

    socket.onmessage = (event) => {
      const newAttack = JSON.parse(event.data);
      
      // Update Arcs (Visuals)
      setArcsData(prev => [...prev.slice(-30), newAttack]);
      
      // Update Sidebar Logs (Information)
      setLogs(prev => [{...newAttack, timestamp: new Date().toLocaleTimeString()}, ...prev.slice(0, 15)]);
    };

    return () => socket.close();
  }, []);

  return (
    <div style={{ backgroundColor: '#000', color: '#00ff41', height: '100vh', overflow: 'hidden', fontFamily: 'Courier New, monospace' }}>
      
      {/* 3D GLOBE LAYER */}
      <Globe
        ref={globeEl}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        arcsData={arcsData}
        arcStartLat={d => d.startLat}
        arcStartLng={d => d.startLng}
        arcEndLat={d => d.endLat}
        arcEndLng={d => d.endLng}
        arcColor={d => d.color}
        arcDashLength={0.4}
        arcDashGap={2}
        arcDashAnimateTime={2000}
        arcStroke={0.5}
      />

      {/* OVERLAY UI: TOP HEADER */}
      <div style={{ position: 'absolute' , top: 0,textAlign: 'center', width: '100%', padding: '20px', background: 'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent)', pointerEvents: "none" }}>
        <h1 style={{ margin: 0, letterSpacing: '4px', textShadow: '0 0 10px #ff0000', color: '#ff4d4d' }}>
          CORE_THREAT_MONITOR_v2.5
        </h1>
        <div style={{ fontSize: '12px', opacity: 0.8 }}>SYSTEM_STATUS: <span style={{color: '#00ff41'}}>ACTIVE_SCANNING</span></div>
      </div>

      {/* OVERLAY UI: LEFT LOG PANEL */}
      <div style={{ 
        position: 'absolute', left: '20px', top: '20px', bottom: '20px', width: '320px', 
        background: 'rgba(0, 20, 0, 0.6)', backdropFilter: 'blur(10px)', border: '1px solid #00ff41',
        padding: '15px', borderRadius: '8px', overflowY: 'hidden', boxShadow: '0 0 20px rgba(0, 255, 65, 0.2)'
      }}>
        <h3 style={{ borderBottom: '1px solid #00ff41', paddingBottom: '5px', fontSize: '14px' }}>INCOMING_INTERCEPTS</h3>
        <div style={{ fontSize: '11px', lineHeight: '1.5em' }}>
          {logs.map((log, i) => (
            <div key={i} style={{ marginBottom: '10px', borderLeft: `3px solid ${log.color}`, paddingLeft: '8px' }}>
              <div style={{ color: log.color, fontWeight: 'bold' }}>[{log.timestamp}] ATTACK_DETECTED</div>
              <div>SOURCE_IP: {log.ip}</div>
              <div>LOC: {log.country} ({log.startLat.toFixed(2)}, {log.startLng.toFixed(2)})</div>
              <div>CONFIDENCE: {log.score}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* OVERLAY UI: STATS BAR */}
      <div style={{ position: 'absolute', right: '20px', bottom: '20px', textAlign: 'right', pointerEvents: 'none' }}>
        <div style={{ fontSize: '40px', fontWeight: 'bold' }}>{arcsData.length}</div>
        <div style={{ fontSize: '10px', letterSpacing: '2px' }}>CONCURRENT_STREAMS</div>
      </div>

    </div>
  );
}

export default App;
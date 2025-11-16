// frontend/src/Panchang/Panchang.jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import tzlookup from 'tz-lookup';
import styles from './Panchang.module.css';
import background from '../assets/video.mp4';

/* ---------- Utilities ---------- */
function pad(n, len = 2) { return String(n).padStart(len, '0'); }

function computeFromSeconds(s) {
  const SEC_PRANA = 4;
  const SEC_VINADI = 24;
  const SEC_GHATI = 24 * 60;
  const SEC_MUHURTA = 48 * 60;
  const DAY = 24 * 3600;
  if (s < 0) s += DAY;
  const totalPranas = Math.floor(s / SEC_PRANA);
  const totalVinadis = Math.floor(s / SEC_VINADI);
  const ghatiCount = Math.floor((s / SEC_GHATI)) % 60;
  const ghatiRem = s % SEC_GHATI;
  const ghatiH = Math.floor(ghatiRem / 3600);
  const ghatiM = Math.floor((ghatiRem % 3600) / 60);
  const ghatiS = Math.floor(ghatiRem % 60);
  const muhurtaCount = Math.floor((s / SEC_MUHURTA)) % 30;
  const muhurtaRem = s % SEC_MUHURTA;
  const muhurtaH = Math.floor(muhurtaRem / 3600);
  const muhurtaM = Math.floor((muhurtaRem % 3600) / 60);
  const muhurtaS = Math.floor(muhurtaRem % 60);
  const vinadiInGhati = Math.floor(ghatiRem / SEC_VINADI);
  const pranaInGhati = Math.floor(ghatiRem / SEC_PRANA);
  return {
    seconds: s,
    totalPranas,
    totalVinadis,
    ghatiCount,
    ghatiH, ghatiM, ghatiS,
    muhurtaCount,
    muhurtaH, muhurtaM, muhurtaS,
    vinadiInGhati,
    pranaInGhati
  };
}

/* ---------- HinduPanel component (side panel) ---------- */
function HinduPanel({ open, onClose, hinduTime }) {
  const [tick, setTick] = useState(null);
  const tickRef = useRef(null);
  const [nowLocal, setNowLocal] = useState(new Date());

  useEffect(() => setNowLocal(new Date()), []);

  useEffect(() => {
    if (!open) {
      if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null; }
      return;
    }
    if (hinduTime && hinduTime.seconds_since_sunrise != null && hinduTime.now_local_iso) {
      const serverNow = new Date(hinduTime.now_local_iso);
      const serverSeconds = Number(hinduTime.seconds_since_sunrise);
      const elapsed = Math.floor((Date.now() - serverNow.getTime()) / 1000);
      setTick(serverSeconds + elapsed);
      tickRef.current = setInterval(() => {
        setTick(prev => prev + 1);
        setNowLocal(new Date());
      }, 1000);
    } else {
      const now = new Date();
      const sr = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 6, 30, 0);
      const base = Math.floor((now.getTime() - sr.getTime()) / 1000);
      const baseWrap = base >= 0 ? base : base + 24 * 3600;
      setTick(baseWrap);
      tickRef.current = setInterval(() => {
        setTick(prev => prev + 1);
        setNowLocal(new Date());
      }, 1000);
    }
    return () => { if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null; } };
  }, [open, hinduTime]);

  const derived = tick != null ? computeFromSeconds(tick) : null;
  if (!open) return null;

  return (
    <div className={`${styles.panelRoot} ${open ? styles.panelOpen : ''}`} aria-hidden={!open}>
      <div className={styles.panelOverlay} onClick={onClose} role="button" aria-label="Close panel overlay"></div>
      <aside className={styles.hinduPanel} role="dialog" aria-modal="true">
        <button className={styles.closeArrow} onClick={onClose} aria-label="Close Hindu panel">‹</button>
        <div className={styles.panelContent}>
          <div className={styles.clockBlock}>
            <div className={styles.clockTitle}>Exact Local Time</div>
            <div className={styles.clockLarge}>{nowLocal.toLocaleTimeString()}</div>
            <div className={styles.clockSub}>{nowLocal.toLocaleDateString()}</div>
          </div>

          <hr className={styles.panelSep} />

          <div className={styles.hinduBlock}>
            <h3 className={styles.hinduTitle}>Hindu Time (from sunrise)</h3>

            <div className={styles.unitRow}>
              <div className={styles.unitLabel}>Sunrise (local)</div>
              <div className={styles.unitValue}>
                {hinduTime?.sunrise_local_iso ? new Date(hinduTime.sunrise_local_iso).toLocaleString() : '06:30 (fallback)'}
              </div>
            </div>

            <div className={styles.unitRow}>
              <div className={styles.unitLabel}>Seconds since sunrise</div>
              <div className={styles.unitValue}>{derived ? derived.seconds : (hinduTime?.seconds_since_sunrise ?? '—')}</div>
            </div>

            <div className={styles.unitRow}>
              <div className={styles.unitLabel}>Ghaṭi (24m)</div>
              <div className={styles.unitValue}>
                {hinduTime?.ghaTi?.count ?? (derived ? derived.ghatiCount : '—')} &nbsp;
                ({derived ? `${pad(derived.ghatiH)}:${pad(derived.ghatiM)}:${pad(derived.ghatiS)}` : (hinduTime?.ghaTi?.in_ghaTi_str ?? '—')})
              </div>
            </div>

            <div className={styles.unitRow}>
              <div className={styles.unitLabel}>Muhūrta (48m)</div>
              <div className={styles.unitValue}>
                {hinduTime?.muhurta?.count ?? (derived ? derived.muhurtaCount : '—')} &nbsp;
                ({derived ? `${pad(derived.muhurtaH)}:${pad(derived.muhurtaM)}:${pad(derived.muhurtaS)}` : (hinduTime?.muhurta?.in_muhurta_str ?? '—')})
              </div>
            </div>

            <div className={styles.unitRow}>
              <div className={styles.unitLabel}>Vinādi (24s)</div>
              <div className={styles.unitValue}>{hinduTime?.vinadi?.in_current_ghaTi ?? (derived ? derived.vinadiInGhati : '—')} in current ghaṭi</div>
            </div>

            <div className={styles.unitRow}>
              <div className={styles.unitLabel}>Prāṇa (4s)</div>
              <div className={styles.unitValue}>
                {hinduTime?.prana?.in_current_ghaTi ?? (derived ? derived.pranaInGhati : '—')} in current ghaṭi
                &nbsp; (total prāṇa: {derived ? derived.totalPranas : (hinduTime?.total_pranas_since_sunrise ?? '—')})
              </div>
            </div>

            <div className={styles.smallNote}>1 ghaṭi = 24 min • 1 muhūrta = 48 min • 1 vinādi = 24 s • 1 prāṇa = 4 s.</div>
          </div>
        </div>
      </aside>
    </div>
  );
}

/* ---------- Main Panchang component (complete) ---------- */
export default function Panchang() {
  const [panchang, setPanchang] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPanchang, setShowPanchang] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);

  const [formData, setFormData] = useState({
    date: new Date().toISOString().slice(0, 10),
    time: '06:30',
    timezone: 'Asia/Kolkata',
    lat: 13.6288,
    lon: 79.4192,
    elev: 151
  });

  const [locStatus, setLocStatus] = useState(''); // messages for geolocation
  const [geoBusy, setGeoBusy] = useState(false);

  async function fetchPanchang(data) {
    try {
      setLoading(true);
      const response = await axios.get('/logic/', {
        params: {
          date: data.date,
          time: data.time,
          timezone: data.timezone,
          lat: data.lat,
          lon: data.lon,
          elev: data.elev
        }
      });
      setPanchang(response.data);
      setShowPanchang(true);
      setShowModal(false);
      setTimeout(() => { document.getElementById('panchangSection')?.scrollIntoView({ behavior: 'smooth' }); }, 100);
      console.log('Panchang fetched:', response.data);
    } catch (error) {
      console.error("Error fetching Panchang:", error);
      // If server responded with JSON error, show it
      if (error.response && error.response.data) {
        const d = error.response.data;
        alert("Panchang fetch failed: " + (d.error || JSON.stringify(d)));
      } else {
        alert("Failed to fetch Panchang data. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit() { fetchPanchang(formData); }
  function clearPanchang() { setShowPanchang(false); setPanchang(null); window.scrollTo({ top: 0, behavior: 'smooth' }); }

  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: (name === 'lat' || name === 'lon' || name === 'elev') ? Number(value) : value
    }));
  }

  // Preset city list
  const presets = [
    { label: 'Tirupati (default)', lat: 13.6288, lon: 79.4192 },
    { label: 'Hyderabad', lat: 17.3850, lon: 78.4867 },
    { label: 'Bengaluru', lat: 12.9716, lon: 77.5946 },
    { label: 'Chennai', lat: 13.0827, lon: 80.2707 },
    { label: 'Mumbai', lat: 19.0760, lon: 72.8777 },
    { label: 'Delhi', lat: 28.6139, lon: 77.2090 },
    { label: 'Kolkata', lat: 22.5726, lon: 88.3639 }
  ];

  function applyPreset(e) {
    const idx = Number(e.target.value);
    if (!isNaN(idx) && presets[idx]) {
      const p = presets[idx];
      setFormData(prev => ({ ...prev, lat: p.lat, lon: p.lon }));
      detectTimezoneAndElevation(p.lat, p.lon);
    }
  }

  // Get timezone from coords using tz-lookup (local)
  function detectTimezoneAndElevation(lat, lon) {
    try {
      setLocStatus('Detecting timezone & elevation...');
      const tz = tzlookup(Number(lat), Number(lon));
      setFormData(prev => ({ ...prev, timezone: tz }));
    } catch (e) {
      console.warn('tz lookup failed', e);
      try {
        const tzb = Intl.DateTimeFormat().resolvedOptions().timeZone;
        setFormData(prev => ({ ...prev, timezone: tzb }));
      } catch (ee) {
        setFormData(prev => ({ ...prev, timezone: 'Asia/Kolkata' }));
      }
    }

    // fetch elevation via open-elevation
    const url = `https://api.open-elevation.com/api/v1/lookup?locations=${lat},${lon}`;
    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data && data.results && data.results[0] && typeof data.results[0].elevation !== 'undefined') {
          setFormData(prev => ({ ...prev, elev: Math.round(data.results[0].elevation) }));
          setLocStatus('Timezone & elevation detected');
        } else {
          setFormData(prev => ({ ...prev, elev: 0 }));
          setLocStatus('Timezone detected, elevation unavailable');
        }
      })
      .catch(err => {
        console.warn('elevation fetch failed', err);
        setFormData(prev => ({ ...prev, elev: 0 }));
        setLocStatus('Timezone detected, elevation fetch failed');
      });
  }

  // Use browser geolocation
  function useMyLocation() {
    if (!navigator.geolocation) {
      setLocStatus('Geolocation not supported by this browser.');
      return;
    }
    setGeoBusy(true);
    setLocStatus('Requesting location...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const lat = Number(latitude.toFixed(6));
        const lon = Number(longitude.toFixed(6));
        setFormData(prev => ({ ...prev, lat, lon }));
        detectTimezoneAndElevation(lat, lon);
        setLocStatus('Location set from device.');
        setGeoBusy(false);
      },
      (err) => {
        console.error('geo error', err);
        setLocStatus('Permission denied or failed to get location.');
        setGeoBusy(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  // when user manually edits lat/lon, re-run timezone/elevation detection after a small debounce
  useEffect(() => {
    const tid = setTimeout(() => {
      detectTimezoneAndElevation(formData.lat, formData.lon);
    }, 700);
    return () => clearTimeout(tid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.lat, formData.lon]);

  return (
    <div className={styles.pageRoot}>
      {!panelOpen && <button className={styles.openArrow} onClick={() => setPanelOpen(true)} aria-label="Open Hindu panel">›</button>}

      <div className={`${styles.mainContent} ${panelOpen ? styles.blurred : ''}`}>
        <video src={background} className={styles.background} muted autoPlay loop></video>
        <div className={styles.hero}>
          <div className={styles.topSection}>
            <h1 className={styles.title}>कालरूपाय नमः शिवाय||</h1>
          </div>
          <div className={styles.videoSpacer}></div>
          <div className={styles.bottomSection}>
            <div className={styles.buttonGroup}>
              <button onClick={() => setShowModal(true)} className={styles.ancientButton} disabled={loading}>
                {loading ? '⏳ Loading...' : '🕉️ Fetch Panchang'}
              </button>

              <button onClick={() => setPanelOpen(true)} className={`${styles.ancientButton} ${styles.panelButton}`}>Open Hindu Clock</button>

              {showPanchang && <button onClick={clearPanchang} className={`${styles.ancientButton} ${styles.clearButton}`}>🗙 Clear</button>}
            </div>
          </div>
        </div>

        {/* Modal */}
        {showModal && (
          <div className={styles.modalOverlay} onClick={() => setShowModal(false)}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
              <h2 className={styles.modalTitle}>Enter Panchang Details</h2>

              <div className={styles.modalBody}>
                <div className={styles.formContainer}>
                  <div className={styles.formRow}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Date</label>
                      <input type="date" name="date" value={formData.date} onChange={handleInputChange} className={styles.input} />
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Time</label>
                      <input type="time" name="time" value={formData.time} onChange={handleInputChange} className={styles.input} />
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Preset Locations</label>
                    <select onChange={applyPreset} className={styles.input}>
                      {presets.map((p, i) => <option key={i} value={i}>{p.label}</option>)}
                    </select>
                  </div>

                  <div className={styles.rowSmall}>
                    <button type="button" className={styles.smallButton} onClick={useMyLocation} disabled={geoBusy}>
                      {geoBusy ? 'Detecting...' : 'Use my location'}
                    </button>
                    <div style={{ marginLeft: 10, fontSize: 12, color: '#444' }}>{locStatus}</div>
                  </div>

                  <div className={styles.formRow}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Latitude</label>
                      <input type="number" step="0.0001" name="lat" value={formData.lat} onChange={handleInputChange} className={styles.input} />
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Longitude</label>
                      <input type="number" step="0.0001" name="lon" value={formData.lon} onChange={handleInputChange} className={styles.input} />
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Timezone (auto-detected)</label>
                    <input type="text" name="timezone" value={formData.timezone} onChange={handleInputChange} className={styles.input} />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Elevation (m) (auto-detected)</label>
                    <input type="number" step="1" name="elev" value={formData.elev} onChange={handleInputChange} className={styles.input} />
                  </div>

                  <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                    Want a map picker? Click <a href="https://www.openstreetmap.org" target="_blank" rel="noreferrer">OpenStreetMap</a>, search a place and copy-paste coordinates here.
                  </div>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button onClick={handleSubmit} className={styles.submitButton}>Calculate Panchang</button>
                <button onClick={() => setShowModal(false)} className={styles.cancelButton}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* Panchang display: ALL CARDS */}
        {showPanchang && panchang && (
          <div id="panchangSection" className={styles.panchangSection}>
            <div className={styles.panchangContainer}>
              <h2 className={styles.sectionTitle}>पञ्चाङ्गम् | Panchang</h2>
              <div className={styles.divider}></div>

              {/* Details card */}
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>📅 Details</h3>
                <div className={styles.grid}>
                  <div className={styles.item}><span className={styles.label}>Date:</span><span className={styles.value}>{panchang.input?.requested_date ?? formData.date}</span></div>
                  <div className={styles.item}><span className={styles.label}>Time:</span><span className={styles.value}>{panchang.input?.requested_time ?? formData.time}</span></div>
                  <div className={styles.item}><span className={styles.label}>Timezone:</span><span className={styles.value}>{panchang.input?.timezone ?? formData.timezone}</span></div>
                  <div className={styles.item}><span className={styles.label}>Location:</span><span className={styles.value}>{panchang.input?.latitude ?? formData.lat}°N, {panchang.input?.longitude ?? formData.lon}°E</span></div>
                  <div className={styles.item}><span className={styles.label}>Elevation:</span><span className={styles.value}>{panchang.input?.elevation_m ?? formData.elev} m</span></div>
                </div>
              </div>

              {/* Instant snapshot */}
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>🌙 Current Moment</h3>
                <div className={styles.grid}>
                  <div className={styles.item}><span className={styles.label}>Tithi:</span><span className={styles.value}>{panchang.instant?.tithi ?? '—'} {panchang.instant?.paksha ? `(${panchang.instant.paksha})` : ''}</span></div>
                  <div className={styles.item}><span className={styles.label}>Nakshatra:</span><span className={styles.value}>{panchang.instant?.nakshatra ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Rashi (Moon):</span><span className={styles.value}>{panchang.instant?.rashi ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Yoga:</span><span className={styles.value}>{panchang.instant?.yoga ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Karana:</span><span className={styles.value}>{panchang.instant?.karana ?? '—'}</span></div>
                </div>
              </div>

              {/* Day-by-sunrise */}
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>🌅 Day (by Sunrise)</h3>
                <div className={styles.grid}>
                  <div className={styles.item}><span className={styles.label}>Sunrise (local):</span><span className={styles.value}>{panchang.day_by_sunrise?.sunrise_local ? new Date(panchang.day_by_sunrise.sunrise_local).toLocaleTimeString() : '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Sunset (local):</span><span className={styles.value}>{panchang.day_by_sunrise?.sunset_local ? new Date(panchang.day_by_sunrise.sunset_local).toLocaleTimeString() : '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Tithi at Sunrise:</span><span className={styles.value}>{panchang.day_by_sunrise?.tithi ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Paksha at Sunrise:</span><span className={styles.value}>{panchang.day_by_sunrise?.paksha ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Nakshatra at Sunrise:</span><span className={styles.value}>{panchang.day_by_sunrise?.nakshatra ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Yoga at Sunrise:</span><span className={styles.value}>{panchang.day_by_sunrise?.yoga ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Rashi (Moon) at Sunrise:</span><span className={styles.value}>{panchang.day_by_sunrise?.rashi_moon ?? '—'}</span></div>
                </div>
              </div>

              {/* Full Moon section */}
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>🌕 Next Full Moon</h3>
                <div className={styles.grid}>
                  <div className={styles.item}><span className={styles.label}>UTC:</span><span className={styles.value}>{panchang.full_moon?.utc ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Local:</span><span className={styles.value}>{panchang.full_moon?.local ? new Date(panchang.full_moon.local).toLocaleString() : '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Nakshatra:</span><span className={styles.value}>{panchang.full_moon?.nakshatra ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Masa (month):</span><span className={styles.value}>{panchang.full_moon?.masa ?? '—'}</span></div>
                </div>
              </div>

              {/* Raw debug block for hindu_time (optional) */}
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>🕰️ Hindu Time (server)</h3>
                <div className={styles.grid}>
                  <div className={styles.item}><span className={styles.label}>Seconds since sunrise:</span><span className={styles.value}>{panchang.hindu_time?.seconds_since_sunrise ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Ghaṭi count:</span><span className={styles.value}>{panchang.hindu_time?.ghaTi?.count ?? '—'}</span></div>
                  <div className={styles.item}><span className={styles.label}>Muhūrta count:</span><span className={styles.value}>{panchang.hindu_time?.muhurta?.count ?? '—'}</span></div>
                </div>
              </div>

              <div className={styles.footer}><p>🕉️ Calculated using server-side Panchang engine (drik - Skyfield)</p></div>
            </div>
          </div>
        )}

      </div>

      {/* Panel */}
      <HinduPanel open={panelOpen} onClose={() => setPanelOpen(false)} hinduTime={panchang?.hindu_time ?? null} />
    </div>
  );
}

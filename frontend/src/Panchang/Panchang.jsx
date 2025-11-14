import { useState } from 'react';
import axios from 'axios';
import styles from './Panchang.module.css';
import background from '../assets/video.mp4';

function Panchang() {
  const [panchang, setPanchang] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPanchang, setShowPanchang] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    date: '2025-11-14',
    time: '10:30',
    timezone: 'Asia/Kolkata'
  });

  async function fetchPanchang(data) {
    try {
      setLoading(true);
      const response = await axios.get('/logic/', {
        params: {
          date: data.date,
          time: data.time,
          timezone: data.timezone
        }
      });
      setPanchang(response.data);
      setShowPanchang(true);
      setShowModal(false);
      setTimeout(() => {
        document.getElementById('panchangSection')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      console.log(response.data);
    } catch (error) {
      console.error("Error fetching Panchang:", error);
      alert("Failed to fetch Panchang data. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit() {
    fetchPanchang(formData);
  }

  function clearPanchang() {
    setShowPanchang(false);
    setPanchang(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  }

  return (
    <div className={styles.container}>
      <video src={background} className={styles.background} muted autoPlay loop></video>
      
      <div className={styles.hero}>
        <div className={styles.topSection}>
          <h1 className={styles.title}>कालरूपाय नमः शिवाय||</h1>
        </div>
        
        <div className={styles.videoSpacer}></div>
        
        <div className={styles.bottomSection}>
          <div className={styles.buttonGroup}>
            <button 
              onClick={() => setShowModal(true)} 
              className={styles.ancientButton}
              disabled={loading}
            >
              {loading ? '⏳ Loading...' : '🕉️ Fetch Panchang'}
            </button>
            
            {showPanchang && (
              <button 
                onClick={clearPanchang} 
                className={`${styles.ancientButton} ${styles.clearButton}`}
              >
                🗙 Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className={styles.modalOverlay} onClick={() => setShowModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Enter Panchang Details</h2>
            <div className={styles.formContainer}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Date</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Time</label>
                <input
                  type="time"
                  name="time"
                  value={formData.time}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Timezone</label>
                <select
                  name="timezone"
                  value={formData.timezone}
                  onChange={handleInputChange}
                  className={styles.input}
                >
                  <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                  <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                </select>
              </div>

              <div className={styles.modalButtons}>
                <button 
                  onClick={handleSubmit} 
                  className={styles.submitButton}
                >
                  Calculate Panchang
                </button>
                <button 
                  onClick={() => setShowModal(false)}
                  className={styles.cancelButton}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showPanchang && panchang && (
        <div id="panchangSection" className={styles.panchangSection}>
          <div className={styles.panchangContainer}>
            <h2 className={styles.sectionTitle}>पञ्चाङ्गम् | Panchang</h2>
            
            <div className={styles.divider}></div>

            {/* Input Info */}
            <div className={styles.card}>
              <h3 className={styles.cardTitle}>📅 Details</h3>
              <div className={styles.grid}>
                <div className={styles.item}>
                  <span className={styles.label}>Date:</span>
                  <span className={styles.value}>{panchang.input.date}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Time:</span>
                  <span className={styles.value}>{panchang.input.time}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Location:</span>
                  <span className={styles.value}>
                    {panchang.input.latitude.toFixed(2)}°N, {panchang.input.longitude.toFixed(2)}°E
                  </span>
                </div>
              </div>
            </div>

            {/* Current Moment */}
            <div className={styles.card}>
              <h3 className={styles.cardTitle}>🌙 Current Moment</h3>
              <div className={styles.grid}>
                <div className={styles.item}>
                  <span className={styles.label}>Tithi:</span>
                  <span className={styles.value}>{panchang.instant.tithi} - {panchang.instant.paksha}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Nakshatra:</span>
                  <span className={styles.value}>{panchang.instant.nakshatra}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Yoga:</span>
                  <span className={styles.value}>{panchang.instant.yoga}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Karana:</span>
                  <span className={styles.value}>{panchang.instant.karana}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Rashi (Moon):</span>
                  <span className={styles.value}>{panchang.instant.rashi}</span>
                </div>
              </div>
            </div>

            {/* Day by Sunrise */}
            <div className={styles.card}>
              <h3 className={styles.cardTitle}>🌅 Day by Sunrise</h3>
              <div className={styles.grid}>
                <div className={styles.item}>
                  <span className={styles.label}>Sunrise:</span>
                  <span className={styles.value}>
                    {new Date(panchang.day_by_sunrise.sunrise_local).toLocaleTimeString('en-IN', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Sunset:</span>
                  <span className={styles.value}>
                    {new Date(panchang.day_by_sunrise.sunset_local).toLocaleTimeString('en-IN', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Tithi at Sunrise:</span>
                  <span className={styles.value}>{panchang.day_by_sunrise.tithi}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Nakshatra at Sunrise:</span>
                  <span className={styles.value}>{panchang.day_by_sunrise.nakshatra}</span>
                </div>
                <div className={styles.item}>
                  <span className={styles.label}>Yoga at Sunrise:</span>
                  <span className={styles.value}>{panchang.day_by_sunrise.yoga}</span>
                </div>
              </div>
            </div>

            {/* Full Moon */}
            {panchang.full_moon && (
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>🌕 Next Full Moon</h3>
                <div className={styles.grid}>
                  <div className={styles.item}>
                    <span className={styles.label}>Date & Time:</span>
                    <span className={styles.value}>
                      {new Date(panchang.full_moon.local).toLocaleDateString('en-IN', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                      {' at '}
                      {new Date(panchang.full_moon.local).toLocaleTimeString('en-IN', {
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                      })}
                    </span>
                  </div>
                  <div className={styles.item}>
                    <span className={styles.label}>Nakshatra:</span>
                    <span className={styles.value}>{panchang.full_moon.nakshatra}</span>
                  </div>
                  <div className={styles.item}>
                    <span className={styles.label}>Masa (Month):</span>
                    <span className={styles.value}>{panchang.full_moon.masa}</span>
                  </div>
                </div>
              </div>
            )}

            <div className={styles.footer}>
              <p>🕉️ Calculated using Drik Panchang System with Lahiri Ayanamsa</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Panchang;
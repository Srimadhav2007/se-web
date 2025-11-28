// frontend/src/Panchang/PlanetChart.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './Panchang.module.css';

// Enhanced planet info with glow colors
const PLANET_INFO = {
  'Sun': { 
    color: '#FFD700', 
    glowColor: '#FFA500',
    symbol: '☉', 
    size: 24,
    name: 'Surya'
  },
  'Moon': { 
    color: '#E6E6FA', 
    glowColor: '#C0C0C0',
    symbol: '☽', 
    size: 22,
    name: 'Chandra'
  },
  'Mercury': { 
    color: '#8C7853', 
    glowColor: '#A0A0A0',
    symbol: '☿', 
    size: 16,
    name: 'Budha'
  },
  'Venus': { 
    color: '#FFC649', 
    glowColor: '#FFD700',
    symbol: '♀', 
    size: 18,
    name: 'Shukra'
  },
  'Mars': { 
    color: '#CD5C5C', 
    glowColor: '#FF6347',
    symbol: '♂', 
    size: 18,
    name: 'Mangala'
  },
  'Jupiter': { 
    color: '#D8CA9D', 
    glowColor: '#F0E68C',
    symbol: '♃', 
    size: 20,
    name: 'Guru'
  },
  'Saturn': { 
    color: '#FAD5A5', 
    glowColor: '#FFE4B5',
    symbol: '♄', 
    size: 20,
    name: 'Shani'
  },
  'Rahu': { 
    color: '#8B4513', 
    glowColor: '#A0522D',
    symbol: '☊', 
    size: 16,
    name: 'Rahu'
  },
  'Ketu': { 
    color: '#4B0082', 
    glowColor: '#6A0DAD',
    symbol: '☋', 
    size: 16,
    name: 'Ketu'
  }
};

// Rashi (Zodiac) names with Sanskrit
const RASHIS = [
  { en: 'Mesha', sa: 'मेष' },
  { en: 'Vrishabha', sa: 'वृषभ' },
  { en: 'Mithuna', sa: 'मिथुन' },
  { en: 'Karka', sa: 'कर्क' },
  { en: 'Simha', sa: 'सिंह' },
  { en: 'Kanya', sa: 'कन्या' },
  { en: 'Tula', sa: 'तुला' },
  { en: 'Vrischika', sa: 'वृश्चिक' },
  { en: 'Dhanu', sa: 'धनु' },
  { en: 'Makara', sa: 'मकर' },
  { en: 'Kumbha', sa: 'कुम्भ' },
  { en: 'Meena', sa: 'मीन' }
];

function PlanetChart({ date, time, timezone, lat, lon, elev }) {
  const [planetData, setPlanetData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('ecliptic');
  const [hoveredPlanet, setHoveredPlanet] = useState(null);
  const [selectedPlanet, setSelectedPlanet] = useState(null);

  useEffect(() => {
    if (date && time) {
      fetchPlanetPositions();
    }
  }, [date, time, timezone, lat, lon, elev]);

  async function fetchPlanetPositions() {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/logic/planets/', {
        params: { date, time, timezone, lat, lon, elev }
      });
      setPlanetData(response.data);
    } catch (err) {
      console.error('Error fetching planet positions:', err);
      setError(err.response?.data?.error || 'Failed to fetch planet positions');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>🪐 Planet Positions</h3>
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ 
            display: 'inline-block',
            width: '50px',
            height: '50px',
            border: '4px solid rgba(212, 175, 55, 0.3)',
            borderTopColor: '#d4af37',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          <p style={{ marginTop: '1rem', color: '#d4af37' }}>Calculating planetary positions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>🪐 Planet Positions</h3>
        <div style={{ color: '#ff4444', padding: '1rem', textAlign: 'center' }}>
          ⚠️ Error: {error}
        </div>
      </div>
    );
  }

  if (!planetData) return null;

  const planets = planetData.planets || {};
  const chartSize = 500;
  const centerX = chartSize / 2;
  const centerY = chartSize / 2;
  const radius = 180;

  // Render tooltip
  function renderTooltip(planetName, planet, x, y) {
    if (!hoveredPlanet || hoveredPlanet !== planetName) return null;
    const info = PLANET_INFO[planetName] || {};
    
    return (
      <div style={{
        position: 'absolute',
        left: `${x + 30}px`,
        top: `${y - 50}px`,
        background: 'rgba(0, 0, 0, 0.95)',
        border: '2px solid #d4af37',
        borderRadius: '8px',
        padding: '1rem',
        minWidth: '200px',
        zIndex: 1000,
        boxShadow: `0 0 20px ${info.glowColor || info.color}`,
        pointerEvents: 'none',
        animation: 'fadeIn 0.2s ease-in'
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.5rem',
          marginBottom: '0.5rem',
          borderBottom: '1px solid rgba(212, 175, 55, 0.3)',
          paddingBottom: '0.5rem'
        }}>
          <span style={{ fontSize: '1.5rem', color: info.color }}>{info.symbol}</span>
          <div>
            <div style={{ fontWeight: 'bold', color: '#d4af37', fontSize: '1.1rem' }}>
              {planetName}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#b8860b' }}>{info.name}</div>
          </div>
        </div>
        <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
          <div><strong style={{ color: '#b8860b' }}>Rashi:</strong> <span style={{ color: '#d4af37' }}>{planet.rashi}</span></div>
          <div><strong style={{ color: '#b8860b' }}>Nakshatra:</strong> <span style={{ color: '#d4af37' }}>{planet.nakshatra}</span></div>
          <div><strong style={{ color: '#b8860b' }}>Longitude:</strong> <span style={{ color: '#d4af37' }}>{planet.ecliptic_longitude.toFixed(2)}°</span></div>
          {viewMode === 'sky' && (
            <>
              <div><strong style={{ color: '#b8860b' }}>Altitude:</strong> <span style={{ color: '#d4af37' }}>{planet.altitude.toFixed(1)}°</span></div>
              <div><strong style={{ color: '#b8860b' }}>Azimuth:</strong> <span style={{ color: '#d4af37' }}>{planet.azimuth.toFixed(1)}°</span></div>
            </>
          )}
        </div>
      </div>
    );
  }

  // Render ecliptic view with enhanced visuals
  function renderEclipticView() {
    return (
      <div style={{ position: 'relative', width: chartSize, height: chartSize, margin: '0 auto' }}>
        <svg 
          width={chartSize} 
          height={chartSize} 
          style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0,
            filter: 'drop-shadow(0 0 10px rgba(212, 175, 55, 0.3))'
          }}
        >
          <defs>
            {/* Glow filter for planets */}
            {Object.entries(PLANET_INFO).map(([name, info]) => (
              <filter key={name} id={`glow-${name}`}>
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            ))}
            {/* Radial gradient for background circle */}
            <radialGradient id="zodiacGradient">
              <stop offset="0%" stopColor="rgba(212, 175, 55, 0.1)" />
              <stop offset="100%" stopColor="rgba(212, 175, 55, 0.01)" />
            </radialGradient>
          </defs>

          {/* Background glow circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius + 10}
            fill="url(#zodiacGradient)"
            opacity="0.5"
          />

          {/* Outer zodiac circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius}
            fill="none"
            stroke="#d4af37"
            strokeWidth="2"
            opacity="0.4"
            strokeDasharray="5,5"
          />
          
          {/* 12 Rashi divisions with enhanced styling */}
          {RASHIS.map((rashi, idx) => {
            const angle = (idx * 30 - 90) * (Math.PI / 180);
            const x1 = centerX + radius * Math.cos(angle);
            const y1 = centerY + radius * Math.sin(angle);
            const x2 = centerX + (radius + 25) * Math.cos(angle);
            const y2 = centerY + (radius + 25) * Math.sin(angle);
            
            return (
              <g key={rashi.en}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#d4af37"
                  strokeWidth="1.5"
                  opacity="0.5"
                />
                <text
                  x={x2 + 15 * Math.cos(angle)}
                  y={y2 + 15 * Math.sin(angle)}
                  fill="#d4af37"
                  fontSize="11"
                  fontWeight="bold"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  style={{ textShadow: '0 0 5px rgba(212, 175, 55, 0.8)' }}
                >
                  {idx + 1}
                </text>
                <text
                  x={x2 + 30 * Math.cos(angle)}
                  y={y2 + 30 * Math.sin(angle)}
                  fill="#b8860b"
                  fontSize="9"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  opacity="0.7"
                >
                  {rashi.sa}
                </text>
              </g>
            );
          })}
          
          {/* Draw planets with enhanced interactivity */}
          {Object.entries(planets).map(([planetName, planet]) => {
            const info = PLANET_INFO[planetName] || { color: '#fff', symbol: '•', size: 12, glowColor: '#fff' };
            const angle = ((planet.ecliptic_longitude - 90) * Math.PI) / 180;
            const distance = radius - 15;
            const x = centerX + distance * Math.cos(angle);
            const y = centerY + distance * Math.sin(angle);
            const isHovered = hoveredPlanet === planetName;
            const isSelected = selectedPlanet === planetName;
            const scale = isHovered || isSelected ? 1.3 : 1;
            
            return (
              <g 
                key={planetName}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredPlanet(planetName)}
                onMouseLeave={() => setHoveredPlanet(null)}
                onClick={() => setSelectedPlanet(selectedPlanet === planetName ? null : planetName)}
              >
                {/* Glow effect */}
                {isHovered && (
                  <circle
                    cx={x}
                    cy={y}
                    r={info.size * 0.8}
                    fill={info.color}
                    opacity="0.3"
                    style={{
                      filter: `blur(8px)`
                    }}
                  />
                )}
                
                {/* Planet circle with gradient */}
                <circle
                  cx={x}
                  cy={y}
                  r={info.size / 2 * scale}
                  fill={info.color}
                  stroke={isSelected ? info.color : (isHovered ? info.color : '#000')}
                  strokeWidth={isSelected ? '3' : (isHovered ? '2' : '1.5')}
                  opacity="0.95"
                  filter={isHovered ? `url(#glow-${planetName})` : 'none'}
                  style={{
                    transition: 'all 0.3s ease',
                    transformOrigin: `${x}px ${y}px`
                  }}
                />
                
                {/* Planet symbol */}
                <text
                  x={x}
                  y={y}
                  fill="#000"
                  fontSize={(info.size - 4) * scale}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  style={{ 
                    pointerEvents: 'none', 
                    fontWeight: 'bold',
                    transition: 'all 0.3s ease'
                  }}
                >
                  {info.symbol}
                </text>
                
                {/* Planet name label */}
                <text
                  x={x}
                  y={y + (info.size / 2) + 12}
                  fill={isHovered ? info.color : '#d4af37'}
                  fontSize={isHovered ? '11' : '10'}
                  fontWeight={isHovered ? 'bold' : 'normal'}
                  textAnchor="middle"
                  dominantBaseline="top"
                  style={{ 
                    pointerEvents: 'none',
                    textShadow: isHovered ? `0 0 8px ${info.color}` : 'none',
                    transition: 'all 0.3s ease'
                  }}
                >
                  {planetName}
                </text>
                
                {/* Line from center to planet when hovered */}
                {isHovered && (
                  <line
                    x1={centerX}
                    y1={centerY}
                    x2={x}
                    y2={y}
                    stroke={info.color}
                    strokeWidth="1"
                    strokeDasharray="3,3"
                    opacity="0.5"
                    style={{ animation: 'drawLine 0.5s ease-out' }}
                  />
                )}
              </g>
            );
          })}
          
          {/* Center Earth with glow */}
          <circle 
            cx={centerX} 
            cy={centerY} 
            r="8" 
            fill="#4a90e2"
            style={{
              filter: 'drop-shadow(0 0 10px rgba(74, 144, 226, 0.8))'
            }}
          />
          <text
            x={centerX}
            y={centerY - 20}
            fill="#4a90e2"
            fontSize="12"
            fontWeight="bold"
            textAnchor="middle"
            dominantBaseline="middle"
            style={{ textShadow: '0 0 8px rgba(74, 144, 226, 0.8)' }}
          >
            Earth
          </text>
        </svg>
        
        {/* Tooltip overlay */}
        {Object.entries(planets).map(([planetName, planet]) => {
          const info = PLANET_INFO[planetName] || {};
          const angle = ((planet.ecliptic_longitude - 90) * Math.PI) / 180;
          const distance = radius - 15;
          const x = centerX + distance * Math.cos(angle);
          const y = centerY + distance * Math.sin(angle);
          return renderTooltip(planetName, planet, x, y);
        })}
      </div>
    );
  }


  // Render sky view with enhanced visuals
  function renderSkyView() {
    return (
      <div style={{ position: 'relative', width: chartSize, height: chartSize, margin: '0 auto' }}>
        <svg width={chartSize} height={chartSize} style={{ position: 'absolute', top: 0, left: 0 }}>
          <defs>
            <radialGradient id="skyGradient">
              <stop offset="0%" stopColor="rgba(74, 144, 226, 0.2)" />
              <stop offset="100%" stopColor="rgba(212, 175, 55, 0.05)" />
            </radialGradient>
          </defs>

          {/* Sky background */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius + 10}
            fill="url(#skyGradient)"
            opacity="0.6"
          />

          {/* Horizon circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius}
            fill="none"
            stroke="#d4af37"
            strokeWidth="2"
            opacity="0.4"
            strokeDasharray="8,4"
          />
          
          {/* Altitude reference circles (30° and 60° above horizon) */}
          {[30, 60].map(alt => {
            const r = radius * (1 - alt / 90);
            return (
              <circle
                key={alt}
                cx={centerX}
                cy={centerY}
                r={r}
                fill="none"
                stroke="#b8860b"
                strokeWidth="1"
                opacity="0.15"
                strokeDasharray="3,6"
              />
            );
          })}
          
          {/* Zenith point */}
          <circle 
            cx={centerX} 
            cy={centerY - radius} 
            r="4" 
            fill="#d4af37"
            style={{
              filter: 'drop-shadow(0 0 8px rgba(212, 175, 55, 0.8))'
            }}
          />
          <text
            x={centerX}
            y={centerY - radius - 15}
            fill="#d4af37"
            fontSize="11"
            fontWeight="bold"
            textAnchor="middle"
            style={{ textShadow: '0 0 8px rgba(212, 175, 55, 0.8)' }}
          >
            Zenith
          </text>
          
          {/* Draw planets in sky view */}
          {Object.entries(planets).map(([planetName, planet]) => {
            const info = PLANET_INFO[planetName] || { color: '#fff', symbol: '•', size: 12, glowColor: '#fff' };
            const alt = planet.altitude;
            const az = planet.azimuth;
            
            if (alt < 0) return null; // Below horizon
            
            const altRad = (alt * Math.PI) / 180;
            const distance = radius * (1 - altRad / (Math.PI / 2));
            const azRad = ((az - 90) * Math.PI) / 180;
            
            const x = centerX + distance * Math.cos(azRad);
            const y = centerY + distance * Math.sin(azRad);
            const isHovered = hoveredPlanet === planetName;
            const scale = isHovered ? 1.3 : 1;
            
            return (
              <g 
                key={planetName}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredPlanet(planetName)}
                onMouseLeave={() => setHoveredPlanet(null)}
                onClick={() => setSelectedPlanet(selectedPlanet === planetName ? null : planetName)}
              >
                {isHovered && (
                  <circle
                    cx={x}
                    cy={y}
                    r={info.size * 0.8}
                    fill={info.color}
                    opacity="0.3"
                    style={{ filter: 'blur(8px)' }}
                  />
                )}
                <circle
                  cx={x}
                  cy={y}
                  r={info.size / 2 * scale}
                  fill={info.color}
                  stroke={isHovered ? info.color : '#000'}
                  strokeWidth={isHovered ? '2' : '1.5'}
                  opacity="0.95"
                  style={{ transition: 'all 0.3s ease' }}
                />
                <text
                  x={x}
                  y={y}
                  fill="#000"
                  fontSize={(info.size - 4) * scale}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  style={{ pointerEvents: 'none', fontWeight: 'bold', transition: 'all 0.3s ease' }}
                >
                  {info.symbol}
                </text>
                <text
                  x={x}
                  y={y + (info.size / 2) + 12}
                  fill={isHovered ? info.color : '#d4af37'}
                  fontSize={isHovered ? '11' : '10'}
                  fontWeight={isHovered ? 'bold' : 'normal'}
                  textAnchor="middle"
                  dominantBaseline="top"
                  style={{ 
                    pointerEvents: 'none',
                    textShadow: isHovered ? `0 0 8px ${info.color}` : 'none',
                    transition: 'all 0.3s ease'
                  }}
                >
                  {planetName}
                </text>
              </g>
            );
          })}
          
          {/* Compass directions with enhanced styling */}
          {['N', 'E', 'S', 'W'].map((dir, idx) => {
            const angle = (idx * 90 - 90) * (Math.PI / 180);
            const x = centerX + (radius + 20) * Math.cos(angle);
            const y = centerY + (radius + 20) * Math.sin(angle);
            return (
              <g key={dir}>
                <line
                  x1={centerX + radius * Math.cos(angle)}
                  y1={centerY + radius * Math.sin(angle)}
                  x2={x}
                  y2={y}
                  stroke="#d4af37"
                  strokeWidth="2"
                  opacity="0.6"
                />
                <circle
                  cx={x}
                  cy={y}
                  r="12"
                  fill="rgba(0, 0, 0, 0.7)"
                  stroke="#d4af37"
                  strokeWidth="2"
                />
                <text
                  x={x}
                  y={y}
                  fill="#d4af37"
                  fontSize="14"
                  fontWeight="bold"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  style={{ textShadow: '0 0 8px rgba(212, 175, 55, 0.8)' }}
                >
                  {dir}
                </text>
              </g>
            );
          })}
        </svg>
        
        {/* Tooltip overlay for sky view */}
        {Object.entries(planets).map(([planetName, planet]) => {
          if (planet.altitude < 0) return null;
          const info = PLANET_INFO[planetName] || {};
          const altRad = (planet.altitude * Math.PI) / 180;
          const distance = radius * (1 - altRad / (Math.PI / 2));
          const azRad = ((planet.azimuth - 90) * Math.PI) / 180;
          const x = centerX + distance * Math.cos(azRad);
          const y = centerY + distance * Math.sin(azRad);
          return renderTooltip(planetName, planet, x, y);
        })}
      </div>
    );
  }

  return (
    <div className={styles.card} style={{ position: 'relative', overflow: 'hidden' }}>
      <h3 className={styles.cardTitle} style={{ marginBottom: '1rem' }}>🪐 Planet Positions</h3>
      
      {/* Enhanced view mode toggle */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        marginBottom: '1.5rem', 
        justifyContent: 'center',
        background: 'rgba(0, 0, 0, 0.3)',
        padding: '0.5rem',
        borderRadius: '8px',
        border: '1px solid rgba(212, 175, 55, 0.2)'
      }}>
        <button
          onClick={() => { setViewMode('ecliptic'); setSelectedPlanet(null); }}
          style={{
            padding: '0.6rem 1.5rem',
            backgroundColor: viewMode === 'ecliptic' ? '#d4af37' : 'transparent',
            color: viewMode === 'ecliptic' ? '#000' : '#d4af37',
            border: '2px solid #d4af37',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: viewMode === 'ecliptic' ? 'bold' : 'normal',
            transition: 'all 0.3s ease',
            boxShadow: viewMode === 'ecliptic' ? '0 0 15px rgba(212, 175, 55, 0.5)' : 'none'
          }}
          onMouseEnter={(e) => {
            if (viewMode !== 'ecliptic') {
              e.target.style.backgroundColor = 'rgba(212, 175, 55, 0.1)';
            }
          }}
          onMouseLeave={(e) => {
            if (viewMode !== 'ecliptic') {
              e.target.style.backgroundColor = 'transparent';
            }
          }}
        >
          🌟 Ecliptic View
        </button>
        <button
          onClick={() => { setViewMode('sky'); setSelectedPlanet(null); }}
          style={{
            padding: '0.6rem 1.5rem',
            backgroundColor: viewMode === 'sky' ? '#d4af37' : 'transparent',
            color: viewMode === 'sky' ? '#000' : '#d4af37',
            border: '2px solid #d4af37',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: viewMode === 'sky' ? 'bold' : 'normal',
            transition: 'all 0.3s ease',
            boxShadow: viewMode === 'sky' ? '0 0 15px rgba(212, 175, 55, 0.5)' : 'none'
          }}
          onMouseEnter={(e) => {
            if (viewMode !== 'sky') {
              e.target.style.backgroundColor = 'rgba(212, 175, 55, 0.1)';
            }
          }}
          onMouseLeave={(e) => {
            if (viewMode !== 'sky') {
              e.target.style.backgroundColor = 'transparent';
            }
          }}
        >
          🌌 Sky View
        </button>
      </div>

      {/* Chart with enhanced container */}
      <div style={{ 
        marginBottom: '2rem',
        padding: '1rem',
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '12px',
        border: '1px solid rgba(212, 175, 55, 0.2)'
      }}>
        {viewMode === 'ecliptic' && renderEclipticView()}
        {viewMode === 'sky' && renderSkyView()}
      </div>

      {/* Enhanced planet details table */}
      <div style={{ overflowX: 'auto' }}>
        <div style={{ 
          marginBottom: '0.5rem', 
          fontSize: '0.85rem', 
          color: '#b8860b',
          textAlign: 'center',
          fontStyle: 'italic'
        }}>
          Click on a planet to highlight it • Hover for details
        </div>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse', 
          fontSize: '0.9rem',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <thead>
            <tr style={{ 
              background: 'linear-gradient(180deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.1))',
              borderBottom: '2px solid #d4af37'
            }}>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#d4af37', fontWeight: 'bold' }}>Planet</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#d4af37', fontWeight: 'bold' }}>Rashi</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#d4af37', fontWeight: 'bold' }}>Nakshatra</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', color: '#d4af37', fontWeight: 'bold' }}>Longitude</th>
              {viewMode === 'sky' && (
                <>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: '#d4af37', fontWeight: 'bold' }}>Altitude</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: '#d4af37', fontWeight: 'bold' }}>Azimuth</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {Object.entries(planets).map(([planetName, planet]) => {
              const info = PLANET_INFO[planetName] || { color: '#fff', symbol: '•' };
              const isSelected = selectedPlanet === planetName;
              
              return (
                <tr 
                  key={planetName}
                  onClick={() => setSelectedPlanet(selectedPlanet === planetName ? null : planetName)}
                  style={{ 
                    borderBottom: '1px solid rgba(212, 175, 55, 0.1)',
                    background: isSelected ? 'rgba(212, 175, 55, 0.15)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'rgba(212, 175, 55, 0.08)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ 
                      color: info.color, 
                      marginRight: '0.5rem',
                      fontSize: '1.2rem',
                      filter: isSelected ? `drop-shadow(0 0 5px ${info.color})` : 'none'
                    }}>
                      {info.symbol}
                    </span>
                    <span style={{ 
                      fontWeight: isSelected ? 'bold' : 'normal',
                      color: isSelected ? info.color : '#d4af37'
                    }}>
                      {planetName}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem', color: '#d4af37' }}>{planet.rashi}</td>
                  <td style={{ padding: '0.75rem', color: '#d4af37' }}>{planet.nakshatra}</td>
                  <td style={{ padding: '0.75rem', color: '#d4af37' }}>{planet.ecliptic_longitude.toFixed(2)}°</td>
                  {viewMode === 'sky' && (
                    <>
                      <td style={{ padding: '0.75rem', color: planet.altitude >= 0 ? '#d4af37' : '#666' }}>
                        {planet.altitude >= 0 ? `${planet.altitude.toFixed(1)}°` : 'Below horizon'}
                      </td>
                      <td style={{ padding: '0.75rem', color: '#d4af37' }}>{planet.azimuth.toFixed(1)}°</td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {/* CSS animations */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes drawLine {
          from { stroke-dashoffset: 100; }
          to { stroke-dashoffset: 0; }
        }
      `}</style>
    </div>
  );
}

export default PlanetChart;

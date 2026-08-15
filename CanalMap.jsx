import React from 'react'

/**
 * Simplified SVG canal layout visualization
 * Reservoir → Main Canal → Head/Middle/Tail Reaches → Villages/Farms
 */
const CANAL_NODES = [
  { id: 'reservoir', label: 'Sardar Sarovar\nReservoir', x: 30,  y: 50, type: 'reservoir', emoji: '🏞️' },
  { id: 'headworks', label: 'Headworks\nInlet',         x: 130, y: 50, type: 'headworks', emoji: '🔧' },

  // Head reach
  { id: 'SNS-H1', label: 'SNS-H1\nVadnagar',  x: 230, y: 20, type: 'sensor_head', emoji: '📡' },
  { id: 'SNS-H2', label: 'SNS-H2\nVisnagar',  x: 330, y: 20, type: 'sensor_head', emoji: '📡' },

  // Middle reach
  { id: 'SNS-M1', label: 'SNS-M1\nPatan',     x: 430, y: 50, type: 'sensor_mid', emoji: '📡' },
  { id: 'SNS-M2', label: 'SNS-M2\nChanasma',  x: 530, y: 50, type: 'sensor_mid', emoji: '📡' },

  // Tail reach
  { id: 'SNS-T1', label: 'SNS-T1\nVijapur',   x: 630, y: 80, type: 'sensor_tail', emoji: '📡' },
  { id: 'SNS-T2', label: 'SNS-T2\nKalol',     x: 730, y: 80, type: 'sensor_tail', emoji: '📡' },
]

const TYPE_COLORS = {
  reservoir:    { fill: '#dbeafe', stroke: '#2563eb', text: '#1d4ed8' },
  headworks:    { fill: '#e0f2fe', stroke: '#0284c7', text: '#0c4a6e' },
  sensor_head:  { fill: '#dbeafe', stroke: '#3b82f6', text: '#1e40af' },
  sensor_mid:   { fill: '#ede9fe', stroke: '#7c3aed', text: '#4c1d95' },
  sensor_tail:  { fill: '#ffedd5', stroke: '#ea580c', text: '#7c2d12' },
}

const CANAL_LINE = [
  [30, 50], [130, 50], [230, 50], [230, 20], [330, 20],  // head branch
  [330, 50], [430, 50], [530, 50],                         // middle branch
  [530, 80], [630, 80], [730, 80],                         // tail branch
]

export default function CanalMap({ sensors = [], scenario = 'normal' }) {
  const getColor = (sensorId) => {
    if (scenario === 'shortage' && sensorId?.includes('T')) return '#ef4444'
    if (scenario === 'anomaly'  && sensorId?.includes('T')) return '#dc2626'
    return null
  }

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox="0 0 820 160" className="w-full min-w-[640px]">
        {/* Canal path */}
        <polyline
          points={CANAL_LINE.map(([x,y]) => `${x},${y}`).join(' ')}
          fill="none"
          stroke="#bfdbfe"
          strokeWidth={6}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Reach labels */}
        {[
          { x: 280, y: 10, label: 'HEAD REACH', color: '#2563eb' },
          { x: 480, y: 42, label: 'MIDDLE REACH', color: '#7c3aed' },
          { x: 680, y: 72, label: 'TAIL REACH', color: '#ea580c' },
        ].map(({ x, y, label, color }) => (
          <text key={label} x={x} y={y} fontSize={9} fill={color} fontWeight="600"
                textAnchor="middle" fontFamily="system-ui">{label}</text>
        ))}

        {/* Sensor nodes */}
        {CANAL_NODES.map((node) => {
          const colors = TYPE_COLORS[node.type] || TYPE_COLORS.sensor_head
          const highlight = getColor(node.id)
          return (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y === 50 ? node.y : node.y + 15}
                r={18}
                fill={highlight || colors.fill}
                stroke={highlight || colors.stroke}
                strokeWidth={2}
              />
              <text
                x={node.x}
                y={(node.y === 50 ? node.y : node.y + 15) + 4}
                fontSize={13}
                textAnchor="middle"
                fontFamily="system-ui"
              >
                {node.emoji}
              </text>
              <text
                x={node.x}
                y={(node.y === 50 ? node.y : node.y + 15) + 28}
                fontSize={8}
                textAnchor="middle"
                fill={colors.text}
                fontFamily="system-ui"
                fontWeight="500"
              >
                {node.label.split('\n')[0]}
              </text>
              <text
                x={node.x}
                y={(node.y === 50 ? node.y : node.y + 15) + 38}
                fontSize={7}
                textAnchor="middle"
                fill="#6b7280"
                fontFamily="system-ui"
              >
                {node.label.split('\n')[1]}
              </text>
            </g>
          )
        })}

        {/* Flow direction arrows */}
        {[[130,50,160,50],[280,50,310,50],[430,50,460,50],[580,80,610,80]].map(([x1,y1,x2,y2], i) => (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#93c5fd" strokeWidth={1.5}
                markerEnd="url(#arrow)" />
        ))}
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#93c5fd" />
          </marker>
        </defs>

        {/* Shortage indicator */}
        {scenario === 'shortage' && (
          <g>
            <rect x={590} y={55} width={130} height={18} rx={4} fill="#fee2e2" stroke="#fca5a5" />
            <text x={655} y={68} fontSize={9} fill="#dc2626" textAnchor="middle" fontWeight="600">
              ⚠ 20% SHORTAGE – TAIL AFFECTED
            </text>
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-2 text-xs text-gray-500">
        {[
          { color: '#dbeafe', border: '#3b82f6', label: '📡 Head Sensor' },
          { color: '#ede9fe', border: '#7c3aed', label: '📡 Middle Sensor' },
          { color: '#ffedd5', border: '#ea580c', label: '📡 Tail Sensor' },
          { color: '#fee2e2', border: '#dc2626', label: '🔴 Shortage Zone' },
        ].map(({ color, border, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full border" style={{ background: color, borderColor: border }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}

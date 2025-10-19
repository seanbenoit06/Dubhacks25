import { useState } from 'react';
import { mockRoutines } from '../data/mockData';
import svgPaths from '../imports/svg-yxbdxs5thx';

interface ReviewPageProps {
  routineId: string;
  segmentId?: string;
  onPracticeAgain: () => void;
  onNextSegment?: () => void;
  onBack: () => void;
  onLearningMode?: () => void;
}

export function ReviewPage({ routineId, segmentId, onPracticeAgain, onBack, onLearningMode }: ReviewPageProps) {
  const routine = mockRoutines.find((r) => r.id === routineId);
  const segment = routine?.segments.find((s) => s.id === segmentId) || routine?.segments[0];

  const [viewMode, setViewMode] = useState<'pose' | 'timing'>('pose');
  const [isPlaying, setIsPlaying] = useState(false);
  const [replayProgress, setReplayProgress] = useState(40);

  const overallAccuracy = 82;
  const timingAccuracy = 79;
  const poseAccuracy = 86;
  const consistency = 82;

  // Mock beat-by-beat performance data (48 beats)
  const beatPerformance = [
    77, 88, 71, 89, 75, 73, 83, 88, 55, 54, 72, 97, 83, 80, 76, 77,
    77, 99, 98, 96, 81, 90, 94, 54, 69, 98, 97, 99, 72, 81, 77, 89,
    94, 96, 95, 76, 88, 71, 76, 73, 91, 81, 73, 79, 99, 83, 98, 71
  ];

  const getGrade = (score: number) => {
    if (score >= 90) return { letter: 'S', emoji: '💎', color: '#00d3f3' };
    if (score >= 80) return { letter: 'A', emoji: '🔥', color: '#05df72' };
    if (score >= 70) return { letter: 'B', emoji: '💫', color: '#f9d949' };
    if (score >= 60) return { letter: 'C', emoji: '⭐', color: '#ff8904' };
    return { letter: 'D', emoji: '💪', color: '#fb2c36' };
  };

  const grade = getGrade(overallAccuracy);

  const getBarColor = (accuracy: number) => {
    if (accuracy >= 80) return '#05df72';
    if (accuracy >= 60) return '#f9d949';
    return '#fb2c36';
  };

  const getBarOpacity = (accuracy: number) => {
    if (accuracy >= 80) return 0.25;
    if (accuracy >= 60) return 0.25;
    return 0.25;
  };

  const corrections = [
    {
      emoji: '🦾',
      title: 'Right Elbow',
      segment: 'Intro',
      beat: 7,
      description: 'Right elbow too low in verse 1',
      severity: 'high' as const
    },
    {
      emoji: '💃',
      title: 'Timing',
      segment: 'Intro',
      beat: 15,
      description: 'Late on beat 15 by ~110 ms',
      severity: 'medium' as const
    },
    {
      emoji: '🦵',
      title: 'Both Knees',
      segment: 'Intro',
      beat: 23,
      description: 'Knee angle off by ~15°',
      severity: 'medium' as const
    }
  ];

  return (
    <div className="bg-gradient-to-b from-[#0b0e16] via-50% via-[#0f1219] to-[#121626] min-h-screen">
      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex gap-4 items-center mb-8">
          <button
            onClick={onBack}
            className="bg-[rgba(255,255,255,0.05)] relative rounded-full shrink-0 size-10 flex items-center justify-center border-[0.8px] border-[rgba(255,255,255,0.1)] hover:bg-[rgba(255,255,255,0.1)] transition-colors"
          >
            <svg className="size-5" fill="none" viewBox="0 0 20 20">
              <path d={svgPaths.p33f6b680} stroke="#99A1AF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.66667" />
              <path d="M15.8333 10H4.16667" stroke="#99A1AF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.66667" />
            </svg>
          </button>
          <div>
            <p className="font-['Arimo',_sans-serif] font-normal leading-5 text-[#99a1af] text-sm tracking-[0.35px] uppercase">
              Performance Summary
            </p>
            <p className="font-['Arimo',_sans-serif] font-normal leading-5 text-sm text-[rgba(255,255,255,0.6)]">
              {routine?.title} - {segment?.name}
            </p>
          </div>
        </div>

        {/* Hero Score Section */}
        <div className="relative mb-8">
          {/* Radial glow background */}
          <div className="absolute inset-0 opacity-30"
            style={{ 
              background: `radial-gradient(ellipse 100% 30% at 50% 20%, rgba(5,223,114,0.2) 0%, rgba(3,112,57,0.1) 25%, rgba(0,0,0,0) 50%)`
            }} 
          />
          
          {/* Main card */}
          <div className="relative bg-gradient-to-b from-[rgba(26,29,46,0.8)] to-[rgba(15,18,25,0.6)] rounded-2xl border-[0.8px] border-[rgba(255,255,255,0.1)] p-8">
            {/* Score and Grade */}
            <div className="flex flex-col items-center mb-8">
              <div className="text-center mb-6">
                <span 
                  className="text-[120px] leading-[120px] tracking-[-3px]"
                  style={{ color: grade.color, textShadow: `0 0 40px ${grade.color}80` }}
                >
                  {overallAccuracy}
                </span>
                <span className="text-[48px] leading-[48px] text-[rgba(255,255,255,0.4)]">%</span>
              </div>
              
              <div className="flex items-center gap-3">
                <span className="text-[60px] leading-[60px]">{grade.emoji}</span>
                <span 
                  className="text-[36px] leading-10 tracking-[1.8px] uppercase"
                  style={{ color: grade.color }}
                >
                  {grade.letter} RANK - GREAT!
                </span>
              </div>
            </div>

            {/* Sub-metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
              {/* Timing */}
              <div className="bg-gradient-to-b from-[rgba(173,70,255,0.1)] to-[rgba(0,0,0,0)] rounded-2xl border-[0.8px] border-[rgba(173,70,255,0.2)] p-4">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="size-5" fill="none" viewBox="0 0 20 20">
                    <path d={svgPaths.p30c3b00} stroke="#A855F7" strokeWidth="1.5" />
                    <path d="M10 6V10L13 13" stroke="#A855F7" strokeLinecap="round" strokeWidth="1.5" />
                  </svg>
                  <span className="font-['Arimo',_sans-serif] text-sm text-[#99a1af] uppercase tracking-[0.35px]">Timing</span>
                </div>
                <p className="font-['Arimo',_sans-serif] text-[30px] leading-9 text-[#c27aff] text-center">{timingAccuracy}%</p>
                <p className="font-['Arimo',_sans-serif] text-xs text-[#6a7282] text-center">Beats on time</p>
              </div>

              {/* Pose */}
              <div className="bg-gradient-to-b from-[rgba(0,184,219,0.1)] to-[rgba(0,0,0,0)] rounded-2xl border-[0.8px] border-[rgba(0,184,219,0.2)] p-4">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="size-5" fill="none" viewBox="0 0 20 20">
                    <path d={svgPaths.p3998eb80} stroke="#00D3F3" strokeLinejoin="round" strokeWidth="1.5" />
                  </svg>
                  <span className="font-['Arimo',_sans-serif] text-sm text-[#99a1af] uppercase tracking-[0.35px]">Pose</span>
                </div>
                <p className="font-['Arimo',_sans-serif] text-[30px] leading-9 text-[#00d3f2] text-center">{poseAccuracy}%</p>
                <p className="font-['Arimo',_sans-serif] text-xs text-[#6a7282] text-center">Avg angle match</p>
              </div>

              {/* Consistency */}
              <div className="bg-gradient-to-b from-[rgba(0,201,80,0.1)] to-[rgba(0,0,0,0)] rounded-2xl border-[0.8px] border-[rgba(0,201,80,0.2)] p-4">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="size-5" fill="none" viewBox="0 0 20 20">
                    <path d={svgPaths.p3ac0b600} stroke="#05DF72" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.66667" />
                    <path d={svgPaths.p3c797180} stroke="#05DF72" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.66667" />
                  </svg>
                  <span className="font-['Arimo',_sans-serif] text-sm text-[#99a1af] uppercase tracking-[0.35px]">Consistency</span>
                </div>
                <p className="font-['Arimo',_sans-serif] text-[30px] leading-9 text-[#05df72] text-center">{consistency}%</p>
                <p className="font-['Arimo',_sans-serif] text-xs text-[#6a7282] text-center">Timing variance</p>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Timeline */}
        <div className="bg-gradient-to-b from-[rgba(26,29,46,0.6)] to-[rgba(15,18,25,0.4)] rounded-2xl border-[0.8px] border-[rgba(255,255,255,0.1)] p-6 mb-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <p className="font-['Arimo',_sans-serif] text-sm text-[#99a1af] uppercase tracking-[0.35px]">Performance Timeline</p>
            
            <div className="bg-[rgba(255,255,255,0.05)] rounded-xl border-[0.8px] border-[rgba(255,255,255,0.1)] p-1 flex gap-1">
              <button
                onClick={() => setViewMode('pose')}
                className={`px-3 h-7 rounded-lg text-xs font-['Arimo',_sans-serif] transition-colors ${
                  viewMode === 'pose' ? 'bg-[rgba(255,255,255,0.1)] text-white' : 'text-[#6a7282] hover:text-white'
                }`}
              >
                Pose Error
              </button>
              <button
                onClick={() => setViewMode('timing')}
                className={`px-3 h-7 rounded-lg text-xs font-['Arimo',_sans-serif] transition-colors ${
                  viewMode === 'timing' ? 'bg-[rgba(255,255,255,0.1)] text-white' : 'text-[#6a7282] hover:text-white'
                }`}
              >
                Timing Error
              </button>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="h-32 relative w-full mb-4">
            {beatPerformance.map((accuracy, idx) => {
              const height = (accuracy / 100) * 128;
              const color = getBarColor(accuracy);
              const isError = accuracy < 70;
              
              return (
                <div
                  key={idx}
                  className="absolute box-border flex flex-col pb-0 rounded-t-md hover:opacity-80 transition-opacity cursor-pointer"
                  style={{
                    backgroundColor: color,
                    height: `${height}px`,
                    left: `${idx * 2.08}%`,
                    top: `${128 - height}px`,
                    width: '1.96%',
                    boxShadow: isError ? `0px 0px 8px 0px ${color}80` : 'none'
                  }}
                >
                  <div className="bg-[rgba(0,0,0,0.9)] h-6 opacity-0 hover:opacity-100 relative rounded-md w-full transition-opacity">
                    <p className="absolute font-['Arimo',_sans-serif] font-normal leading-4 left-2 text-xs text-white top-1 whitespace-nowrap">
                      Beat {idx}: {Math.round(accuracy)}%
                    </p>
                    {isError && (
                      <p className="absolute font-['Arimo',_sans-serif] font-normal leading-3 left-2 text-[#ff6467] text-[10px] top-5">
                        Error detected
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Timeline labels */}
          <div className="flex justify-between">
            <span className="font-['Arimo',_sans-serif] text-xs text-[#6a7282]">0s</span>
            <span className="font-['Arimo',_sans-serif] text-xs text-[#6a7282]">199s</span>
          </div>
        </div>

        {/* Top 3 Corrections */}
        <div className="bg-gradient-to-b from-[rgba(26,29,46,0.6)] to-[rgba(15,18,25,0.4)] rounded-2xl border-[0.8px] border-[rgba(255,255,255,0.1)] p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <svg className="size-4" fill="none" viewBox="0 0 16 16">
              <path d={svgPaths.p39ee6532} stroke="#C27AFF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.33333" />
              <path d="M8 5.33333V8" stroke="#C27AFF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.33333" />
              <path d="M8 10.6667H8.00667" stroke="#C27AFF" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.33333" />
            </svg>
            <p className="font-['Arimo',_sans-serif] text-sm text-[#99a1af] uppercase tracking-[0.35px]">Top 3 Corrections</p>
          </div>

          <div className="flex flex-col gap-3">
            {corrections.map((correction, idx) => (
              <div
                key={idx}
                className={`rounded-2xl p-4 ${
                  correction.severity === 'high'
                    ? 'bg-[rgba(251,44,54,0.1)] border-[0.8px] border-[rgba(251,44,54,0.3)]'
                    : 'bg-[rgba(240,177,0,0.1)] border-[0.8px] border-[rgba(240,177,0,0.3)]'
                }`}
              >
                <div className="flex gap-3">
                  <span className="text-[30px] leading-9">{correction.emoji}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-['Arimo',_sans-serif] text-base leading-6 text-[rgba(255,255,255,0.9)]">
                        {correction.title}
                      </span>
                      <div className="bg-[rgba(255,255,255,0.05)] rounded-lg border-[0.8px] border-[rgba(255,255,255,0.2)] px-2 py-1">
                        <span className="font-['Arimo',_sans-serif] text-xs text-neutral-50">
                          {correction.segment}, beat {correction.beat}
                        </span>
                      </div>
                    </div>
                    <p className="font-['Arimo',_sans-serif] text-sm leading-5 text-[#99a1af] mb-3">
                      {correction.description}
                    </p>
                    <button className="flex items-center gap-1 hover:opacity-80 transition-opacity">
                      <svg className="size-3" fill="none" viewBox="0 0 12 12">
                        <path d={svgPaths.p32f38800} stroke="#00D3F2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <span className="font-['Arimo',_sans-serif] text-xs leading-4 text-[#00d3f2]">Watch</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Buttons */}
        <div className="flex gap-4">
          {onLearningMode && (
            <button
              onClick={onLearningMode}
              className="flex-1 bg-gradient-to-r from-[#ad46ff] via-[#f6339a] to-[#00d3f3] h-10 rounded-lg shadow-lg flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
            >
              <span className="text-lg">🎓</span>
              <span className="font-['Arimo',_sans-serif] text-sm text-white uppercase tracking-wider">Enter Learning Mode</span>
            </button>
          )}

          <button
            onClick={onPracticeAgain}
            className="flex-1 bg-gradient-to-r from-[#00b8db] to-[#ad46ff] h-10 rounded-lg shadow-lg flex items-center justify-center hover:opacity-90 transition-opacity"
          >
            <svg className="size-4 mr-2" fill="none" viewBox="0 0 16 16">
              <path d={svgPaths.p12949080} stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.33333" />
              <path d="M2 2V5.33333H5.33333" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.33333" />
            </svg>
            <span className="font-['Arimo',_sans-serif] text-sm text-white">Retry</span>
          </button>

          <button
            onClick={onBack}
            className="flex-1 bg-[rgba(38,38,38,0.3)] h-10 rounded-lg border-[0.8px] border-neutral-800 flex items-center justify-center hover:bg-[rgba(38,38,38,0.5)] transition-colors"
          >
            <svg className="size-4 mr-2" fill="none" viewBox="0 0 16 16">
              <path d={svgPaths.p33f6b680} stroke="#FAFAFA" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.66667" />
              <path d="M15.8333 10H4.16667" stroke="#FAFAFA" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.66667" />
            </svg>
            <span className="font-['Arimo',_sans-serif] text-sm text-neutral-50">Go Back to Main Page</span>
          </button>
        </div>
      </div>
    </div>
  );
}

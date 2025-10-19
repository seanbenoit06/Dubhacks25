import { useState, useEffect, useRef } from 'react';
import { mockRoutines } from '../data/mockData';
import { PracticeTip } from '../types';
import { motion, AnimatePresence } from 'motion/react';
import { Play, SkipForward } from 'lucide-react';

// Import our new components and services
import { VideoPlayer } from '../components/VideoPlayer';
import { LiveCameraView } from '../components/LiveCameraView';
import { LiveFeedback } from '../components/LiveFeedback';
import { PracticeControlBar } from '../components/PracticeControlBar';
import { useVideoBeatSync } from '../hooks/useVideoBeatSync';
import { useSnapshotCapture } from '../hooks/useSnapshotCapture';
import { mockFeedbackService, MockFeedbackResponse } from '../services/mockFeedbackService';

interface EnhancedPracticePageProps {
  routineId: string;
  onBack: () => void;
  onReview: () => void;
  onSettings: () => void;
}

export function EnhancedPracticePage({ routineId, onBack, onReview, onSettings }: EnhancedPracticePageProps) {
  const routine = mockRoutines.find((r) => r.id === routineId);
  
  // Video state
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSkeleton, setShowSkeleton] = useState(false);

  // Camera and feedback state
  const [ghostOpacity, setGhostOpacity] = useState(60);
  const [mirrorCamera, setMirrorCamera] = useState(true);
  const [hasStarted, setHasStarted] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [currentFeedback, setCurrentFeedback] = useState<MockFeedbackResponse | null>(null);
  const [overallAccuracy, setOverallAccuracy] = useState(82);

  // Video reference
  const videoSrc = `/videos/${routine?.title.toLowerCase()}.mp4`; // Assuming video files in public/videos

  if (!routine) {
    return <div>Routine not found</div>;
  }

  const totalBeats = routine.segments.reduce((acc, seg) => acc + seg.beats, 0);
  const errorRegions = [8, 9, 15, 23, 24];

  // Use video-beat sync hook
  const { state: beatState } = useVideoBeatSync({
    bpm: routine.bpm,
    totalBeats,
    videoCurrentTime,
    videoDuration,
    onBeatChange: (beat) => {
      // Beat changes are handled automatically by the hook
      console.log('Beat changed to:', beat);
    },
  });

  // Use snapshot capture hook
  const {
    captureSnapshot,
    processQueue,
    queueStatus,
    isCapturing,
    startAutoCapture,
    stopAutoCapture
  } = useSnapshotCapture({
    autoCapture: true,
    captureInterval: 500,
    onSnapshotProcessed: (result) => {
      console.log('Snapshot processed:', result);
    },
    onError: (error) => {
      console.error('Snapshot error:', error);
    }
  });

  // Handle camera snapshot
  const handleSnapshot = async (snapshot: string) => {
    if (!hasStarted) return;

    try {
      // Process with mock feedback service (replace with real API later)
      const feedback = await mockFeedbackService.processSnapshot(snapshot, {
        baseScore: 0.75,
        feedbackFrequency: 0.3,
        includeErrors: true
      });

      setCurrentFeedback(feedback);
      
      // Update overall accuracy based on combined score
      if (feedback.comparison_result) {
        const newAccuracy = Math.round(feedback.comparison_result.combined_score * 100);
        setOverallAccuracy(newAccuracy);
      }

      console.log('Feedback received:', feedback);
    } catch (error) {
      console.error('Error processing snapshot:', error);
    }
  };

  // Debug logging for timeline
  useEffect(() => {
    console.log('Timeline Debug:', {
      videoCurrentTime,
      videoDuration,
      currentBeat: beatState.currentBeat,
      totalBeats,
      bpm: routine.bpm,
      beatProgress: beatState.beatProgress
    });
  }, [videoCurrentTime, beatState.currentBeat, beatState.beatProgress]);

  const handleStart = () => {
    setCountdown(3);
  };

  useEffect(() => {
    if (countdown === null) return;
    
    if (countdown === 0) {
      setTimeout(() => {
        setCountdown(null);
        setHasStarted(true);
        setIsPlaying(true);
        startAutoCapture();
      }, 500);
      return;
    }

    const timer = setTimeout(() => {
      setCountdown(countdown - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [countdown, startAutoCapture]);

  // Generate current tip from feedback
  const currentTip: PracticeTip | undefined = currentFeedback?.live_feedback ? {
    joint: 'General',
    message: currentFeedback.live_feedback,
    beatIndex: beatState.currentBeat,
  } : undefined;

  return (
    <div className="relative h-screen w-full overflow-hidden" style={{ backgroundImage: "linear-gradient(rgb(11, 14, 22) 0%, rgb(15, 18, 25) 50%, rgb(18, 22, 38) 100%), linear-gradient(90deg, rgb(255, 255, 255) 0%, rgb(255, 255, 255) 100%)" }}>
      {/* Skip to Summary Button */}
      {hasStarted && (
        <button
          onClick={onReview}
          className="absolute top-6 right-6 z-40 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg border border-white/20 text-white text-sm flex items-center gap-2 transition-all backdrop-blur-sm"
        >
          <SkipForward className="w-4 h-4" />
          Skip to Summary
        </button>
      )}

      {/* Start Button Overlay */}
      <AnimatePresence>
        {!hasStarted && countdown === null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md"
          >
            <motion.button
              onClick={handleStart}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative group"
            >
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 blur-2xl opacity-60 group-hover:opacity-80 transition-opacity" />
              <div className="relative flex items-center gap-4 px-12 py-6 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full">
                <Play className="w-8 h-8 text-white" />
                <span className="text-white text-2xl uppercase tracking-wider">Start Practice</span>
              </div>
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Countdown Overlay */}
      <AnimatePresence>
        {countdown !== null && countdown > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
          >
            <motion.div
              key={countdown}
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.5, opacity: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="relative"
            >
              <div 
                className="absolute inset-0 blur-3xl opacity-80"
                style={{
                  background: `radial-gradient(circle, ${
                    countdown === 3 ? '#22d3ee' : countdown === 2 ? '#a855f7' : '#ec4899'
                  } 0%, transparent 70%)`
                }}
              />
              <div 
                className="relative text-[200px] leading-none"
                style={{
                  color: countdown === 3 ? '#22d3ee' : countdown === 2 ? '#a855f7' : '#ec4899',
                  textShadow: `0 0 40px ${countdown === 3 ? '#22d3ee' : countdown === 2 ? '#a855f7' : '#ec4899'}`
                }}
              >
                {countdown}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative w-full max-w-[1159.2px] h-full">
          {/* Beat Timeline at Top */}
          <div className="absolute bg-gradient-to-b from-[#1a1d2e] h-[80px] left-0 to-[rgba(0,0,0,0)] top-0 w-full">
            <div aria-hidden="true" className="absolute border-[0px_0px_0.8px] border-[rgba(255,255,255,0.05)] border-solid inset-0 pointer-events-none" />
          
            {/* Segments */}
            <div className="absolute h-[79.2px] left-0 top-0 w-full flex">
              {routine.segments.map((segment, idx) => {
                const width = (segment.beats / totalBeats) * 100;
                return (
                  <div
                    key={segment.id}
                    className="box-border h-[79.2px] relative"
                    style={{ width: `${width}%` }}
                  >
                    <div aria-hidden="true" className="absolute border-[0px_0.8px_0px_0px] border-[rgba(255,255,255,0.05)] border-solid inset-0 pointer-events-none" />
                    <div className="absolute left-[12px] top-[12px]">
                      <p className="font-['Arimo',_sans-serif] font-normal leading-[16px] text-[#99a1af] text-[12px] tracking-[0.3px] uppercase">
                        {segment.name}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Beat Ticks */}
            <div className="absolute h-[79.2px] left-0 top-0 w-full flex">
              {Array.from({ length: totalBeats }).map((_, beatIdx) => {
                const isStrongBeat = beatIdx % 4 === 0;
                const isErrorBeat = errorRegions.includes(beatIdx);
                const position = (beatIdx / totalBeats) * 100;
                
                return (
                  <div
                    key={beatIdx}
                    className={`absolute ${
                      isErrorBeat
                        ? 'bg-[#fb2c36] h-[32px] shadow-[0px_0px_8px_0px_rgba(239,68,68,0.6)] top-[35.2px]'
                        : isStrongBeat
                        ? 'bg-[rgba(255,255,255,0.4)] h-[24px] top-[43.2px]'
                        : 'bg-[rgba(255,255,255,0.15)] h-[12px] top-[55.2px]'
                    } w-px`}
                    style={{ left: `${position}%` }}
                  />
                );
              })}
            </div>

            {/* Playhead */}
            <div
              className="absolute bg-[#00d3f3] h-[79.2px] shadow-[0px_0px_20px_0px_rgba(34,211,238,0.8),0px_0px_40px_0px_rgba(34,211,238,0.4)] top-0 w-[3px] transition-all duration-100"
              style={{ left: `${Math.min((beatState.currentBeat / totalBeats) * 100, 100)}%` }}
            >
              <div className="bg-[#00d3f3] h-[12px] rounded-[2.68435e+07px] shadow-[0px_0px_12px_0px_#22d3ee,0px_0px_24px_0px_rgba(34,211,238,0.6)] w-full" />
            </div>

            {/* Beat Counter */}
            <div className="absolute h-[15.988px] left-[16px] top-[51.2px]">
              <p className="font-['Arimo',_sans-serif] font-normal leading-[16px] text-[#6a7282] text-[12px]">
                Beat {beatState.currentBeat}
              </p>
            </div>
            <div className="absolute h-[15.988px] right-[16px] top-[51.2px]">
              <p className="font-['Arimo',_sans-serif] font-normal leading-[16px] text-[#6a7282] text-[12px]">
                {totalBeats} beats total
              </p>
            </div>
          </div>

          {/* Three Column Layout - User, Live Feedback, Performer */}
          <div className="absolute h-[594.4px] left-[24px] top-[80px] w-[1111.2px]">
            {/* Left: User View */}
            <div className="absolute bg-gradient-to-b from-[#0b0e16] h-[537px] left-[24px] rounded-[10px] to-[#121626] top-[21px] w-[400.025px]">
              <div className="h-[537px] overflow-clip relative rounded-[inherit] w-full">
                <div className="absolute left-[16.8px] top-[16.8px] z-10">
                  <p className="font-['Arimo',_sans-serif] font-normal leading-[16px] text-[#6a7282] text-[12px] tracking-[0.6px] uppercase">
                    User
                  </p>
                </div>
                {/* Live Camera Feed */}
                <LiveCameraView 
                  className="absolute inset-0 rounded-[inherit] w-full h-full"
                  onSnapshot={handleSnapshot}
                  autoSnapshot={hasStarted && isCapturing}
                  snapshotInterval={500}
                  showMirrorButton={false}
                />
              </div>
              <div aria-hidden="true" className="absolute border-[0.8px] border-[rgba(255,255,255,0.05)] border-solid inset-0 pointer-events-none rounded-[10px]" />
            </div>

            {/* Center: Live Feedback Column */}
            <div className="absolute bg-gradient-to-b from-[#0b0e16] h-[537px] left-[466px] rounded-[10px] to-[#121626] top-[24px] w-[156px]">
              <LiveFeedback 
                overallAccuracy={overallAccuracy}
                currentTip={currentTip}
                isPlaying={isPlaying}
              />
              <div aria-hidden="true" className="absolute border-[0.8px] border-[rgba(255,255,255,0.05)] border-solid inset-0 pointer-events-none rounded-[10px]" />
            </div>

            {/* Right: Reference Video */}
            <div className="absolute bg-gradient-to-b from-[#0b0e16] h-[537px] left-[673px] rounded-[10px] to-[#121626] top-[24px] w-[438px]">
              <div className="h-[537px] overflow-clip relative rounded-[inherit] w-full">
                <div className="absolute left-[301.15px] top-[16.8px]">
                  <p className="font-['Arimo',_sans-serif] font-normal leading-[16px] text-[#6a7282] text-[12px] tracking-[0.6px] uppercase">
                    Reference
                  </p>
                </div>
                {/* Video Player */}
                <VideoPlayer
                  videoSrc={videoSrc}
                  isPlaying={isPlaying}
                  currentTime={videoCurrentTime}
                  duration={videoDuration}
                  onTimeUpdate={setVideoCurrentTime}
                  onLoadedMetadata={setVideoDuration}
                  onPlayPause={() => setIsPlaying(!isPlaying)}
                  onRestart={() => {
                    setVideoCurrentTime(0);
                    setIsPlaying(true);
                  }}
                  playbackRate={playbackRate}
                  mirror={false}
                  showSkeleton={showSkeleton}
                  className="w-full h-full"
                />
              </div>
              <div aria-hidden="true" className="absolute border-[0.8px] border-[rgba(255,255,255,0.05)] border-solid inset-0 pointer-events-none rounded-[10px]" />
            </div>
          </div>

          {/* Control Bar */}
          <div className="absolute bg-gradient-to-b from-[#0f1219] h-[80.8px] left-0 to-[#0f1219] top-[674.4px] via-50% via-[#13161f] w-full">
            <PracticeControlBar
              isPlaying={isPlaying}
              onPlayPause={() => setIsPlaying(!isPlaying)}
              onRestart={() => {
                setVideoCurrentTime(0);
                setIsPlaying(true);
              }}
              onRecalibrate={() => {
                // Recalibrate camera
                console.log('Recalibrating camera...');
              }}
              onSettings={onSettings}
              fps={30}
              warnings={[]}
              ghostOpacity={ghostOpacity}
              onGhostOpacityChange={setGhostOpacity}
              mirrorCamera={mirrorCamera}
              onMirrorToggle={() => setMirrorCamera(!mirrorCamera)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

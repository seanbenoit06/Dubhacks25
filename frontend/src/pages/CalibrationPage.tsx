import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { CheckCircle2, Circle, User } from 'lucide-react';

interface CalibrationPageProps {
  onComplete: () => void;
  onBack: () => void;
}

export function CalibrationPage({ onComplete, onBack }: CalibrationPageProps) {
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const checklistItems = [
    { id: 1, label: 'Stand 6-8 feet back from camera', completed: false },
    { id: 2, label: 'Full body visible in frame', completed: false },
    { id: 3, label: 'Good lighting (no backlight)', completed: false },
    { id: 4, label: 'Clear background space', completed: false },
  ];

  const [checklist, setChecklist] = useState(checklistItems);

  const handleCalibrate = () => {
    setIsCalibrating(true);
    
    // Simulate calibration process
    setTimeout(() => {
      const updatedChecklist = checklist.map(item => ({ ...item, completed: true }));
      setChecklist(updatedChecklist);
      setIsCalibrating(false);
      setIsComplete(true);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-4xl w-full space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] bg-clip-text text-transparent">
            Camera Calibration
          </h1>
          <p className="text-muted-foreground">
            Let's set up your camera for the best tracking experience
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Left: Camera Preview */}
          <Card className="p-6 bg-card border-border">
            <div className="space-y-4">
              <h3>Camera Preview</h3>
              
              {/* T-Pose Silhouette */}
              <div className="relative aspect-[3/4] bg-black rounded-lg border border-border overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  {/* Background grid */}
                  <div className="absolute inset-0 opacity-10">
                    <div className="w-full h-full" style={{
                      backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(255, 255, 255, .05) 25%, rgba(255, 255, 255, .05) 26%, transparent 27%, transparent 74%, rgba(255, 255, 255, .05) 75%, rgba(255, 255, 255, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 255, 255, .05) 25%, rgba(255, 255, 255, .05) 26%, transparent 27%, transparent 74%, rgba(255, 255, 255, .05) 75%, rgba(255, 255, 255, .05) 76%, transparent 77%, transparent)',
                      backgroundSize: '50px 50px'
                    }} />
                  </div>

                  {/* T-Pose Guide */}
                  <div className="relative z-10 flex flex-col items-center text-center">
                    <User className="w-32 h-32 text-purple-500/50 mb-4" />
                    <div className="text-sm text-muted-foreground bg-black/50 px-4 py-2 rounded-lg">
                      Stand in T-pose position
                    </div>
                  </div>

                  {/* Frame guide */}
                  <div className="absolute inset-4 border-2 border-dashed border-purple-500/30 rounded-lg" />
                </div>
              </div>

              <div className="text-xs text-center text-muted-foreground">
                Camera feed placeholder - align yourself within the frame
              </div>
            </div>
          </Card>

          {/* Right: Checklist */}
          <div className="space-y-6">
            <Card className="p-6 bg-card border-border">
              <h3 className="mb-4">Setup Checklist</h3>
              <div className="space-y-3">
                {checklist.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                      item.completed
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-muted/20'
                    }`}
                  >
                    {item.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                    )}
                    <span className={item.completed ? 'text-foreground' : 'text-muted-foreground'}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Tips Card */}
            <Card className="p-6 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/30">
              <h4 className="mb-2 text-blue-300">💡 Pro Tips</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Wear fitted clothing for better tracking</li>
                <li>• Avoid busy patterns or reflective materials</li>
                <li>• Clear the area around you for full movement</li>
              </ul>
            </Card>

            {/* Action Buttons */}
            <div className="space-y-3">
              {!isComplete ? (
                <Button
                  size="lg"
                  onClick={handleCalibrate}
                  disabled={isCalibrating}
                  className="w-full bg-[var(--neon-purple)] hover:bg-[var(--neon-purple)]/90"
                >
                  {isCalibrating ? (
                    <>
                      <div className="animate-spin mr-2 h-5 w-5 border-2 border-current border-t-transparent rounded-full" />
                      Calibrating...
                    </>
                  ) : (
                    'Start Calibration'
                  )}
                </Button>
              ) : (
                <Button
                  size="lg"
                  onClick={onComplete}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
                >
                  <CheckCircle2 className="w-5 h-5 mr-2" />
                  Begin Practice
                </Button>
              )}

              <Button
                variant="outline"
                size="lg"
                onClick={onBack}
                className="w-full border-border"
              >
                Back to Library
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client"

import { useEffect, useRef, useState } from "react"
import { Camera, Check, Loader2, Pause, Play, WifiOff } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

export default function SignLanguageTranslator() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const [isStreaming, setIsStreaming] = useState(false)
  const [prediction, setPrediction] = useState<string>("")
  const [accuracy, setAccuracy] = useState<number>(0)
  const [isLoading, setIsLoading] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [wsStatus, setWsStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected")
  const [handDetected, setHandDetected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  
  const frameRate = 5
  
  // Connect to WebSocket server
  const connectWebSocket = () => {
    // Clear any previous connection errors
    setConnectionError(null);
    setWsStatus("connecting");

    // Close any existing connection
    if (wsRef.current && 
        (wsRef.current.readyState === WebSocket.OPEN || 
         wsRef.current.readyState === WebSocket.CONNECTING)) {
      wsRef.current.close();
    }

    try {
      // Try connecting directly to the Python backend first
      const ws = new WebSocket("ws://localhost:8000/ws");
      
      // Set timeout to detect connection issues
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          setConnectionError("Connection timeout. Please check if the backend server is running.");
          setWsStatus("disconnected");
        }
      }, 5000);

      ws.onopen = () => {
        console.log("WebSocket connection established");
        clearTimeout(connectionTimeout);
        setWsStatus("connected");
        setConnectionError(null);
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Received message:", data);
          
          // Update hand detection status
          const hasHands = data.handDetected !== undefined ? data.handDetected : !!data.prediction;
          setHandDetected(hasHands);
          
          // Process prediction data
          if (!hasHands || !data.prediction) {
            setPrediction("");
            setAccuracy(0);
          } else {
            setPrediction(data.prediction);
            if (data.confidence) {
              setAccuracy(Math.round(data.confidence * 100));
            }
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      }

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionError("Failed to connect to the server. Please check if the backend is running.");
        setWsStatus("disconnected");
        clearTimeout(connectionTimeout);
      }

      ws.onclose = (event) => {
        console.log("WebSocket connection closed:", event.code, event.reason);
        setWsStatus("disconnected");
        // Only set error if it wasn't already set by onerror
        if (!connectionError && event.code !== 1000) {
          setConnectionError(`Connection closed (Code: ${event.code}). ${event.reason || "Please try reconnecting."}`);
        }
        // Clear all data when connection closes
        setPrediction("");
        setAccuracy(0);
        setHandDetected(false);
        clearTimeout(connectionTimeout);
      }

      wsRef.current = ws;
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setConnectionError("Failed to create WebSocket connection. Please try again.");
      setWsStatus("disconnected");
    }
  }

  // Disconnect WebSocket
  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setWsStatus("disconnected");
      // Clear all data when disconnecting
      setPrediction("");
      setAccuracy(0);
      setHandDetected(false);
      setConnectionError(null);
    }
  }

  // Capture and send frames to the backend
  const captureAndSendFrame = () => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    if (!context) return;

    try {
      // Set canvas dimensions to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw current video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert canvas to base64 image (JPEG format with quality 0.7 for reduced size)
      const base64Image = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];

      // Send the frame to the backend
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            frame: base64Image,
            timestamp: Date.now(),
          }),
        );
      }
    } catch (error) {
      console.error("Error capturing or sending frame:", error);
    }
  }

  // Start or stop the camera stream
  const toggleCamera = async () => {
    if (isStreaming) {
      // Stop the stream
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
        videoRef.current.srcObject = null;
        setIsStreaming(false);
        setPrediction("");
        setAccuracy(0);
        setHandDetected(false);
        disconnectWebSocket();
      }
    } else {
      // Start the stream
      setIsLoading(true);
      setCameraError(null);

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "user",
            width: { ideal: 640 },
            height: { ideal: 480 },
          },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setIsStreaming(true);

          // Connect to WebSocket after camera starts
          connectWebSocket();
        }
      } catch (err) {
        console.error("Error accessing camera:", err);
        setCameraError("Could not access camera. Please ensure you've granted camera permissions.");
      } finally {
        setIsLoading(false);
      }
    }
  }

  // Set up frame capture interval when streaming starts
  useEffect(() => {
    let frameInterval: NodeJS.Timeout | null = null;

    if (isStreaming && wsStatus === "connected") {
      // Calculate interval in milliseconds based on desired frame rate
      const intervalMs = 1000 / frameRate;

      frameInterval = setInterval(() => {
        captureAndSendFrame();
      }, intervalMs);
    }

    return () => {
      if (frameInterval) {
        clearInterval(frameInterval);
      }
    }
  }, [isStreaming, wsStatus]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
      disconnectWebSocket();
    }
  }, []);

  return (
    <main className="container mx-auto py-6 px-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Camera Section */}
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  <Camera className="h-5 w-5" />
                  Camera Feed
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      wsStatus === "connected" ? "success" : wsStatus === "connecting" ? "outline" : "destructive"
                    }
                  >
                    {wsStatus === "connected"
                      ? "Connected to Model"
                      : wsStatus === "connecting"
                        ? "Connecting..."
                        : "Disconnected"}
                  </Badge>
                </div>
              </div>
              <CardDescription>Position your hands in the frame to translate sign language</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <div className="relative w-full aspect-video bg-muted rounded-lg overflow-hidden mb-4">
                {cameraError ? (
                  <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-muted-foreground">
                    {cameraError}
                  </div>
                ) : !isStreaming ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Camera className="h-16 w-16 text-muted-foreground opacity-20" />
                  </div>
                ) : null}
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`w-full h-full object-cover ${!isStreaming ? "hidden" : ""}`}
                />
                {/* Hidden canvas used for frame capture */}
                <canvas ref={canvasRef} className="hidden" />
              </div>

              {connectionError && (
                <div className="w-full p-3 mb-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
                  {connectionError}
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3 w-full">
                <Button
                  onClick={toggleCamera}
                  disabled={isLoading}
                  variant={isStreaming ? "destructive" : "default"}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Initializing Camera
                    </>
                  ) : isStreaming ? (
                    <>
                      <Pause className="mr-2 h-4 w-4" />
                      Stop Camera
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Start Camera
                    </>
                  )}
                </Button>

                {isStreaming && wsStatus !== "connected" && (
                  <Button onClick={connectWebSocket} variant="outline" className="w-full">
                    <WifiOff className="mr-2 h-4 w-4" />
                    Reconnect to Model
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Prediction Section */}
        <div>
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Translation Results</CardTitle>
              <CardDescription>Real-time sign language detection</CardDescription>
            </CardHeader>
            <CardContent>
              {isStreaming ? (
                <>
                  <div className="mb-8">
                    <h3 className="text-sm font-medium mb-2">Detected Sign</h3>
                    <div className="bg-primary/10 rounded-lg p-6 text-center">
                      {handDetected ? (
                        prediction ? (
                          <p className="text-3xl font-bold text-primary">{prediction}</p>
                        ) : (
                          <p className="text-muted-foreground">Recognizing sign...</p>
                        )
                      ) : (
                        <p className="text-muted-foreground">No hand detected. Please show a hand sign.</p>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <h3 className="text-sm font-medium">Confidence Level</h3>
                      <span className="text-sm font-medium">{accuracy}%</span>
                    </div>
                    <Progress value={accuracy} className="h-2" />

                    <div className="mt-6 flex items-center gap-2 text-sm text-muted-foreground">
                      {handDetected ? (
                        accuracy > 80 ? (
                          <>
                            <Check className="h-4 w-4 text-green-500" />
                            <span>High confidence prediction</span>
                          </>
                        ) : accuracy > 60 ? (
                          <>
                            <Check className="h-4 w-4 text-yellow-500" />
                            <span>Medium confidence prediction</span>
                          </>
                        ) : accuracy > 0 ? (
                          <>
                            <Check className="h-4 w-4 text-red-500" />
                            <span>Low confidence prediction</span>
                          </>
                        ) : (
                          <span>Analyzing hand position...</span>
                        )
                      ) : (
                        <span>Waiting for hand to appear in frame...</span>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-[300px] text-center text-muted-foreground">
                  <Camera className="h-12 w-12 mb-4 opacity-20" />
                  <p>Start the camera to begin translating sign language</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}

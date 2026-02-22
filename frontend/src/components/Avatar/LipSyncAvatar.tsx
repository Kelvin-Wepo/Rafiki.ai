/**
 * LipSyncAvatar Component
 * Displays the Rafiki avatar with real-time lip-sync animation
 * Uses video playback for pre-generated lip-sync, with canvas fallback
 */

import { useRef, useEffect, useState } from 'react';
import avatarImage from '../../assets/rafiki_avatar.png';

interface LipSyncAvatarProps {
  audioLevel: number; // 0-100
  isSpeaking: boolean;
  isListening: boolean;
  size?: number;
  videoUrl?: string; // Pre-generated lip-sync video URL
}

export default function LipSyncAvatar({ 
  audioLevel, 
  isSpeaking, 
  isListening,
  size = 280,
  videoUrl
}: LipSyncAvatarProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const animationRef = useRef<number>(0);
  const [imageLoaded, setImageLoaded] = useState(false);
  
  // Smoothed audio level for natural lip movement
  const smoothedLevelRef = useRef(0);
  
  // Mouth position calibrated from MediaPipe FaceLandmarker detection
  const MOUTH_CENTER_X = 0.50;
  const MOUTH_CENTER_Y = 0.635;
  
  // Load avatar image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      imageRef.current = img;
      setImageLoaded(true);
    };
    img.src = avatarImage;
  }, []);
  
  // Determine if video should be used - derived from props, no effect needed
  const shouldUseVideo = Boolean(videoUrl);
  
  // Handle video URL changes - load video when URL is provided
  useEffect(() => {
    if (videoUrl && videoRef.current) {
      videoRef.current.src = videoUrl;
      videoRef.current.load();
    }
  }, [videoUrl]);
  
  // Play/pause video based on speaking state
  useEffect(() => {
    if (shouldUseVideo && videoRef.current) {
      if (isSpeaking) {
        videoRef.current.play().catch(console.error);
      } else {
        videoRef.current.pause();
        videoRef.current.currentTime = 0;
      }
    }
  }, [isSpeaking, shouldUseVideo]);
  
  // Animate the avatar with subtle lip-sync effect
  useEffect(() => {
    // Skip canvas animation if using video
    if (shouldUseVideo) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx || !imageLoaded || !imageRef.current) return;
    
    const animate = (time: number) => {
      // Smooth the audio level for natural movement
      const targetLevel = isSpeaking ? audioLevel : 0;
      smoothedLevelRef.current += (targetLevel - smoothedLevelRef.current) * 0.3;
      
      // Clear and draw base image
      ctx.clearRect(0, 0, size, size);
      ctx.drawImage(imageRef.current!, 0, 0, size, size);
      
      // Subtle visual feedback when speaking
      if (isSpeaking && smoothedLevelRef.current > 3) {
        const intensity = Math.min(smoothedLevelRef.current / 100, 1);
        
        // Mouth region parameters
        const mouthX = size * MOUTH_CENTER_X;
        const mouthY = size * MOUTH_CENTER_Y;
        const mouthRegionWidth = size * 0.15;
        const mouthRegionHeight = size * 0.08;
        
        // Subtle mouth opening effect using darken blend
        ctx.save();
        ctx.globalCompositeOperation = 'multiply';
        
        // Create gradient for natural mouth interior
        const gradient = ctx.createRadialGradient(
          mouthX, mouthY, 0,
          mouthX, mouthY, mouthRegionWidth * (0.3 + intensity * 0.4)
        );
        gradient.addColorStop(0, `rgba(60, 30, 30, ${0.2 + intensity * 0.5})`);
        gradient.addColorStop(0.6, `rgba(80, 40, 40, ${0.1 + intensity * 0.3})`);
        gradient.addColorStop(1, 'rgba(100, 50, 50, 0)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        
        // Draw mouth opening shape
        const openAmount = intensity * mouthRegionHeight * 0.8;
        const wobble = Math.sin(time * 0.015) * 1.5;
        
        ctx.ellipse(
          mouthX + wobble * 0.3,
          mouthY + openAmount * 0.3,
          mouthRegionWidth * (0.5 + intensity * 0.3),
          mouthRegionHeight * (0.3 + intensity * 0.5),
          0, 0, Math.PI * 2
        );
        ctx.fill();
        ctx.restore();
        
        // Add subtle highlight above mouth (upper lip)
        if (intensity > 0.3) {
          ctx.save();
          ctx.globalCompositeOperation = 'soft-light';
          ctx.fillStyle = `rgba(180, 100, 100, ${intensity * 0.3})`;
          ctx.beginPath();
          ctx.ellipse(
            mouthX,
            mouthY - mouthRegionHeight * 0.5,
            mouthRegionWidth * 0.4,
            mouthRegionHeight * 0.2,
            0, Math.PI, 0
          );
          ctx.fill();
          ctx.restore();
        }
      }
      
      // Add listening glow effect
      if (isListening) {
        ctx.save();
        const pulseIntensity = (Math.sin(time * 0.005) + 1) * 0.5;
        const gradient = ctx.createRadialGradient(
          size / 2, size / 2, size * 0.35,
          size / 2, size / 2, size * 0.5
        );
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0)');
        gradient.addColorStop(0.7, `rgba(59, 130, 246, ${0.05 + pulseIntensity * 0.1})`);
        gradient.addColorStop(1, `rgba(59, 130, 246, ${0.15 + pulseIntensity * 0.15})`);
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);
        ctx.restore();
      }
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animationRef.current = requestAnimationFrame(animate);
    
    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [imageLoaded, audioLevel, isSpeaking, isListening, size, shouldUseVideo, MOUTH_CENTER_X, MOUTH_CENTER_Y]);
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Video element for pre-generated lip-sync */}
      {shouldUseVideo && (
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover rounded-full"
          muted={false}
          playsInline
          loop
        />
      )}
      
      {/* Canvas for real-time animation */}
      {!shouldUseVideo && (
        <canvas
          ref={canvasRef}
          width={size}
          height={size}
          className="rounded-full"
          style={{
            width: size,
            height: size,
          }}
        />
      )}
      
      {/* Fallback image while loading */}
      {!imageLoaded && !shouldUseVideo && (
        <img
          src={avatarImage}
          alt="Rafiki AI Assistant"
          className="absolute inset-0 w-full h-full object-cover rounded-full"
        />
      )}
    </div>
  );
}

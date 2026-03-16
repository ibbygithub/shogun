"use client";

import { useEffect, useRef, useState } from "react";

export interface MediaViewerProps {
  url: string;
  title: string;
  onClose: () => void;
}

function resolveEmbedUrl(url: string): { embedUrl: string | null; isYouTubeSearch: boolean } {
  // YouTube watch → embed
  const ytWatch = url.match(/youtube\.com\/watch\?.*v=([^&]+)/);
  if (ytWatch) {
    return { embedUrl: `https://www.youtube.com/embed/${ytWatch[1]}`, isYouTubeSearch: false };
  }

  // YouTube short links
  const ytShort = url.match(/youtu\.be\/([^?]+)/);
  if (ytShort) {
    return { embedUrl: `https://www.youtube.com/embed/${ytShort[1]}`, isYouTubeSearch: false };
  }

  // YouTube search results — cannot be embedded
  if (url.includes("youtube.com/results")) {
    return { embedUrl: null, isYouTubeSearch: true };
  }

  // Google Maps → embed
  const mapsQ = url.match(/maps\.google\.com\/\?q=([^&]+)/);
  if (mapsQ) {
    return { embedUrl: `https://maps.google.com/maps?q=${mapsQ[1]}&output=embed`, isYouTubeSearch: false };
  }
  const mapsPlace = url.match(/google\.com\/maps\/place\/([^/]+)/);
  if (mapsPlace) {
    return { embedUrl: `https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d0!3d0!4d0!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s!2s${encodeURIComponent(url)}`, isYouTubeSearch: false };
  }

  // Default: try direct iframe
  return { embedUrl: url, isYouTubeSearch: false };
}

function getSiteName(url: string): string {
  try {
    const hostname = new URL(url).hostname.replace(/^www\./, "");
    return hostname;
  } catch {
    return url;
  }
}

export default function MediaViewer({ url, title, onClose }: MediaViewerProps) {
  const { embedUrl, isYouTubeSearch } = resolveEmbedUrl(url);
  const [loadError, setLoadError] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Close on ESC key
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  // Close on backdrop click
  function handleOverlayClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === overlayRef.current) onClose();
  }

  const siteName = getSiteName(url);

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10000,
        background: "rgba(0,0,0,0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
    >
      <div style={{
        background: "white",
        borderRadius: "12px",
        overflow: "hidden",
        width: "100%",
        maxWidth: "900px",
        maxHeight: "90vh",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 8px 40px rgba(0,0,0,0.35)",
      }}>
        {/* Title bar */}
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          borderBottom: "1px solid #e5e7eb",
          background: "#f8fafc",
          flexShrink: 0,
        }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
            <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "#111827" }}>{title}</span>
            <span style={{ fontSize: "0.72rem", color: "#6b7280" }}>{siteName}</span>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: "0.75rem",
                color: "#1d4ed8",
                textDecoration: "none",
                padding: "4px 10px",
                borderRadius: "6px",
                border: "1px solid #bfdbfe",
                background: "#eff6ff",
                fontWeight: 600,
              }}
            >
              Open in tab ↗
            </a>
            <button
              onClick={onClose}
              style={{
                background: "none",
                border: "none",
                fontSize: "1.25rem",
                cursor: "pointer",
                color: "#6b7280",
                lineHeight: 1,
                padding: "2px 6px",
                borderRadius: "4px",
              }}
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content area */}
        <div style={{ flex: 1, overflow: "hidden", minHeight: "400px", position: "relative" }}>
          {isYouTubeSearch ? (
            /* YouTube search results cannot be embedded */
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              gap: "1rem",
              padding: "2rem",
              color: "#374151",
              textAlign: "center",
            }}>
              <div style={{ fontSize: "2rem" }}>▶</div>
              <p style={{ fontSize: "0.9rem", maxWidth: "360px" }}>
                YouTube search results cannot be shown inline.
              </p>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  background: "#ff0000",
                  color: "white",
                  padding: "0.5rem 1.25rem",
                  borderRadius: "8px",
                  fontWeight: 700,
                  textDecoration: "none",
                  fontSize: "0.875rem",
                }}
              >
                Open YouTube ↗
              </a>
            </div>
          ) : loadError ? (
            /* Generic load error */
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              gap: "1rem",
              padding: "2rem",
              color: "#374151",
              textAlign: "center",
            }}>
              <p style={{ fontSize: "0.9rem" }}>
                This site cannot be shown inline.
              </p>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  background: "#1d4ed8",
                  color: "white",
                  padding: "0.5rem 1.25rem",
                  borderRadius: "8px",
                  fontWeight: 700,
                  textDecoration: "none",
                  fontSize: "0.875rem",
                }}
              >
                Open in new tab ↗
              </a>
            </div>
          ) : (
            <iframe
              src={embedUrl ?? url}
              title={title}
              style={{ width: "100%", height: "100%", border: "none", minHeight: "460px" }}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              onError={() => setLoadError(true)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

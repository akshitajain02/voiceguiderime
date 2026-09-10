// src/liveKitConnection.js
// VoiceGuide LiveKit Connection Manager
// Handles Room connection, microphone publishing, audio playback of agent TTS,
// and data-channel screen content synchronization.

import {
  Room,
  RoomEvent,
  Track,
  ConnectionState,
} from "livekit-client";

export class VoiceGuideConnection {
  /**
   * @param {Object} options
   * @param {string} [options.tokenServerUrl="http://localhost:8000/token"] - Backend token generation endpoint
   * @param {(state: string) => void} [options.onStateChange] - Callback for connection state changes
   * @param {(speaking: { isLocalSpeaking: boolean, isAgentSpeaking: boolean }) => void} [options.onSpeakingChange] - Callback for speech activity
   * @param {(error: Error) => void} [options.onError] - Error callback
   */
  constructor({
    tokenServerUrl = (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1")
      ? "/api/token"
      : "http://localhost:8000/token",
    onStateChange,
    onSpeakingChange,
    onError,
  } = {}) {
    this.tokenServerUrl = tokenServerUrl;
    this.callbacks = {
      onStateChange,
      onSpeakingChange,
      onError,
    };

    this.room = null;
    this.audioElements = new Set();
    this.isConnected = false;
    this.isConnecting = false;
  }

  /**
   * Fetch a join token and server URL from the backend token server.
   * @param {Object} params
   * @param {string} [params.room="voiceguide-room"]
   * @param {string} [params.identity]
   * @returns {Promise<{ token: string, url: string, room: string, identity: string }>}
   */
  async fetchToken({ room = "voiceguide-room", identity } = {}) {
    const url = new URL(this.tokenServerUrl);
    url.searchParams.set("room", room);
    if (identity) {
      url.searchParams.set("identity", identity);
    }

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Token server responded with status: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Connect to the LiveKit room, publish microphone, and set up audio output.
   * @param {Object} [options]
   * @param {string} [options.serverUrl]
   * @param {string} [options.token]
   * @param {string} [options.room="voiceguide-room"]
   * @param {string} [options.identity]
   */
  async connect({
    serverUrl,
    token,
    room = "voiceguide-room",
    identity,
  } = {}) {
    if (this.isConnected || this.isConnecting) {
      console.warn("VoiceGuide is already connecting or connected.");
      return;
    }

    this.isConnecting = true;
    this.callbacks.onStateChange?.("connecting");

    try {
      // 1. Fetch token and url if not provided
      let connectUrl = serverUrl;
      let connectToken = token;

      if (!connectUrl || !connectToken) {
        const tokenData = await this.fetchToken({ room, identity });
        connectUrl = tokenData.url;
        connectToken = tokenData.token;
      }

      // 2. Initialize LiveKit Room
      this.room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // 3. Register Room event listeners
      this.room.on(RoomEvent.Connected, () => {
        this.isConnected = true;
        this.isConnecting = false;
        this.callbacks.onStateChange?.("connected");
      });

      this.room.on(RoomEvent.Disconnected, () => {
        this.cleanupAudio();
        this.isConnected = false;
        this.isConnecting = false;
        this.callbacks.onStateChange?.("disconnected");
      });

      // Handle remote tracks (Agent's TTS audio stream)
      this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === Track.Kind.Audio) {
          const audioElement = track.attach();
          audioElement.autoplay = true;
          audioElement.style.display = "none";
          document.body.appendChild(audioElement);
          this.audioElements.add(audioElement);
        }
      });

      this.room.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach().forEach((el) => {
          this.audioElements.delete(el);
          el.remove();
        });
      });

      // Handle active speaker changes (detect who is speaking)
      this.room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const isLocalSpeaking = speakers.some((s) => s.isLocal);
        const isAgentSpeaking = speakers.some((s) => !s.isLocal);
        this.callbacks.onSpeakingChange?.({ isLocalSpeaking, isAgentSpeaking });
      });

      // 4. Connect to Room
      await this.room.connect(connectUrl, connectToken);

      // 5. Publish microphone audio track
      try {
        await this.room.localParticipant.setMicrophoneEnabled(true);
      } catch (micErr) {
        console.warn("Microphone access failed or was denied:", micErr);
        this.callbacks.onError?.(micErr);
      }

      return this.room;
    } catch (err) {
      this.isConnected = false;
      this.isConnecting = false;
      this.cleanupAudio();
      this.callbacks.onStateChange?.("disconnected");
      this.callbacks.onError?.(err);
      throw err;
    }
  }

  /**
   * Send extracted screen content to the LiveKit agent via reliable data-channel.
   * Format matches backend agent's expectation: { "screen_content": ... }
   * @param {Object} screenContent
   * @returns {Promise<boolean>}
   */
  async sendScreenContent(screenContent) {
    if (!this.room || this.room.state !== ConnectionState.Connected) {
      console.warn("Cannot send screen content: Room is not connected.");
      return false;
    }

    try {
      const payload = JSON.stringify({
        screen_content: screenContent,
      });
      const encoder = new TextEncoder();
      await this.room.localParticipant.publishData(encoder.encode(payload), {
        reliable: true,
      });
      return true;
    } catch (err) {
      console.error("Failed to send screen content via data channel:", err);
      this.callbacks.onError?.(err);
      return false;
    }
  }

  /**
   * Disconnect from the room and clean up all audio elements.
   */
  async disconnect() {
    this.cleanupAudio();

    if (this.room) {
      try {
        if (this.room.localParticipant) {
          await this.room.localParticipant.setMicrophoneEnabled(false);
        }
        await this.room.disconnect();
      } catch (err) {
        console.warn("Error during room disconnect:", err);
      } finally {
        this.room = null;
      }
    }

    this.isConnected = false;
    this.isConnecting = false;
    this.callbacks.onStateChange?.("disconnected");
  }

  /**
   * Remove and clean up attached audio elements from the DOM.
   */
  cleanupAudio() {
    for (const el of this.audioElements) {
      try {
        el.pause();
        el.srcObject = null;
        el.remove();
      } catch (_) {}
    }
    this.audioElements.clear();
  }
}

export default VoiceGuideConnection;

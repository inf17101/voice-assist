

const audio_output_component = document.getElementById("audio_output_component_id");
                     
async function setupWebRTC(peerConnection) {
          
    // Get audio stream from webcam
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
            "sampleRate": 16000,
            "channelCount": 1,
            "echoCancellation": true,
            "noiseSuppression": true,
            "autoGainControl": false,
            "facingMode": true,
        },
    })

    const audioContext = new AudioContext();
    const gainNode = audioContext.createGain();

    // Set your desired gain (1 = original volume, 3 = 3x volume, etc.)
    gainNode.gain.value = 3.0; // 3x gain
    
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(gainNode);

    // Create a new MediaStream with the amplified audio
    const amplifiedStream = audioContext.createMediaStreamDestination();
    gainNode.connect(amplifiedStream);
    
    //  Send audio stream to server
    amplifiedStream.stream.getTracks().forEach(async (track) => {
        const sender = pc.addTrack(track, stream);
    })
    
    
    peerConnection.addEventListener("track", (evt) => {
        if (audio_output_component && 
            audio_output_component.srcObject !== evt.streams[0]) {
            audio_output_component.srcObject = evt.streams[0];
        }
    });
    
    // Create data channel (needed!)
    const dataChannel = peerConnection.createDataChannel("text");

    // Create and send offer
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    let webrtc_id = Math.random().toString(36).substring(7)

    // Send ICE candidates to server
    // (especially needed when server is behind firewall)
    peerConnection.onicecandidate = ({ candidate }) => {
        if (candidate) {
            console.debug("Sending ICE candidate", candidate);
            fetch('/webrtc/offer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                candidate: candidate.toJSON(),
                webrtc_id: webrtc_id,
                type: "ice-candidate",
                    })
                })
            }
    };

    // Send offer to server
    const response = await fetch('/webrtc/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sdp: offer.sdp,
            type: offer.type,
            webrtc_id: webrtc_id
        })
    });

    // Handle server response
    const serverResponse = await response.json();
    await peerConnection.setRemoteDescription(serverResponse);
}
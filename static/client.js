

const audio_output_component = document.getElementById("audio_output_component_id");
                     
async function setupWebRTC(peerConnection) {
          
    // Get audio stream from webcam
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
    })
    
    
    //  Send audio stream to server
    stream.getTracks().forEach(async (track) => {
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
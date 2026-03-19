// chat.js — Real-time chat functionality using Socket.IO + voice recording

// Global variables
var socket = null;  // Will hold the Socket.IO connection
var mediaRecorder = null;  // Will hold the MediaRecorder for voice messages
var audioChunks = [];  // Stores recorded audio data chunks
var currentRoomId = null;  // The current chat room ID

/**
 * initChat — Called from chat.html to initialize the real-time chat.
 * @param {number} roomId — The chat room ID
 * @param {number} userId — The current logged-in user's ID
 * @param {string} userName — The current user's name
 */
function initChat(roomId, userId, userName) {
    currentRoomId = roomId;

    // Connect to the Flask-SocketIO server
    socket = io();

    // Join the specific room
    socket.emit('join', { room: roomId });

    // Listen for incoming messages from the server
    socket.on('receive_message', function(data) {
        appendMessage(data, userId);  // Add the message to the chat box
    });

    // Handle the message form submission
    var form = document.getElementById('messageForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();  // Prevent the page from reloading
        var input = document.getElementById('messageInput');
        var message = input.value.trim();  // Get the text and remove whitespace

        if (message !== '') {
            // Send message through SocketIO to the server
            socket.emit('send_message', {
                room: roomId,
                message: message
            });
            input.value = '';  // Clear the input field
        }
    });

    // Voice recording button
    var voiceBtn = document.getElementById('voiceBtn');
    var stopVoice = document.getElementById('stopVoice');
    var voiceStatus = document.getElementById('voiceStatus');

    voiceBtn.addEventListener('click', function() {
        startRecording(voiceStatus, voiceBtn);
    });

    stopVoice.addEventListener('click', function() {
        stopRecording(roomId, voiceStatus, voiceBtn);
    });

    // Auto-scroll to the bottom of the chat box
    scrollToBottom();
}

/**
 * appendMessage — Adds a new message bubble to the chat box.
 */
function appendMessage(data, currentUserId) {
    var chatBox = document.getElementById('chatBox');
    var isSent = (data.sender_id == currentUserId);

    var wrapper = document.createElement('div');
    wrapper.className = 'd-flex align-items-center ' + (isSent ? 'justify-content-end' : '');
    if (data.msg_id) {
        wrapper.id = 'msg-container-' + data.msg_id;
    }

    // Add delete button if it's our message
    if (isSent && data.msg_id) {
        var deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm text-danger opacity-50 px-2 py-1 border-0 shadow-none mx-1';
        deleteBtn.title = 'Delete Message';
        deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
        deleteBtn.onclick = function() { deleteMessage(data.msg_id); };
        wrapper.appendChild(deleteBtn);
    }

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + (isSent ? 'msg-sent' : 'msg-received');

    if (data.message_type === 'voice' && data.file_path) {
        // Voice message: show audio player
        bubble.innerHTML = '<audio controls src="/static/' + data.file_path + '"></audio>';
    } else {
        // Text message
        bubble.textContent = data.message;
    }

    // Timestamp
    var timeDiv = document.createElement('div');
    timeDiv.className = 'text-end';
    timeDiv.innerHTML = '<small style="font-size:0.7rem;opacity:0.7;">' + data.sent_at + '</small>';
    bubble.appendChild(timeDiv);

    wrapper.appendChild(bubble);
    chatBox.appendChild(wrapper);

    scrollToBottom();  // Scroll down to show the newest message
}

/**
 * deleteMessage — Sends an API request to delete the message and removes it from the UI.
 */
function deleteMessage(msgId) {
    if (!confirm("Delete this message for everyone?")) return;
    
    fetch('/delete_message/' + msgId, {
        method: 'POST'
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            var el = document.getElementById('msg-container-' + msgId);
            if (el) el.remove();
        } else {
            alert("Could not delete message.");
        }
    })
    .catch(function(err) {
        alert("Error deleting message.");
    });
}

/**
 * scrollToBottom — Scrolls the chat box to the very bottom.
 */
function scrollToBottom() {
    var chatBox = document.getElementById('chatBox');
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * startRecording — Begins recording audio using the browser's MediaRecorder API.
 */
function startRecording(voiceStatus, voiceBtn) {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = function(e) {
                audioChunks.push(e.data);  // Collect audio data
            };

            mediaRecorder.start();  // Start recording
            voiceStatus.style.display = 'block';  // Show "Recording..." status
            voiceBtn.disabled = true;  // Disable the mic button while recording
        })
        .catch(function(err) {
            alert('Microphone access denied or not available.');
        });
}

/**
 * stopRecording — Stops the recording and uploads the audio file to the server.
 */
function stopRecording(roomId, voiceStatus, voiceBtn) {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();

        mediaRecorder.onstop = function() {
            // Create a Blob (binary large object) from the recorded chunks
            var blob = new Blob(audioChunks, { type: 'audio/webm' });
            var formData = new FormData();
            formData.append('voice', blob, 'voice_message.webm');

            // Upload via AJAX to the Flask route
            fetch('/upload_voice/' + roomId, {
                method: 'POST',
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    // Broadcast voice message to room via SocketIO
                    socket.emit('send_message', {
                        room: roomId,
                        message: '',
                        message_type: 'voice',
                        file_path: data.file_path,
                        msg_id: data.msg_id
                    });
                }
            })
            .catch(function(err) {
                alert('Failed to send voice message.');
            });

            voiceStatus.style.display = 'none';  // Hide recording status
            voiceBtn.disabled = false;  // Re-enable mic button
        };
    }
}

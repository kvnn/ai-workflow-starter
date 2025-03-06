export function connectToWebSocket(url: string, onMessage: (data: any) => void): WebSocket {
  const socket = new WebSocket(url);

  socket.onopen = () => {
    console.log('WebSocket connected');
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  socket.onclose = () => {
    console.log('WebSocket disconnected');
  };

  return socket;
}

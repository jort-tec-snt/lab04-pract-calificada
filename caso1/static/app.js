const form = document.querySelector('#download-form');
const button = document.querySelector('#submit');
const statusBox = document.querySelector('#status');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  button.disabled = true;
  statusBox.dataset.state = 'loading';
  statusBox.textContent = 'Preparando el video… Mantén esta página abierta. Puede tardar hasta 3 minutos.';
  try {
    const response = await fetch('/download', { method: 'POST', body: new URLSearchParams(new FormData(form)) });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'No se pudo completar la descarga.');
    }
    const blob = await response.blob();
    const name = response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'video.mp4';
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    statusBox.dataset.state = 'success';
    statusBox.textContent = `Video recibido: ${name} (${(blob.size / 1048576).toFixed(1)} MiB). Revisa las descargas de tu navegador.`;
  } catch (error) {
    statusBox.dataset.state = 'error';
    statusBox.textContent = error.message || 'Se perdió la conexión con la aplicación.';
  } finally {
    button.disabled = false;
  }
});

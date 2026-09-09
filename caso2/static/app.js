const form = document.querySelector('#record-form');
const operator = document.querySelector('#operator');
const statusBox = document.querySelector('#status');
const exportButton = document.querySelector('#export');
const extractButton = document.querySelector('#extract');
const fields = ['dni', 'miembro', 'nombres', 'region', 'provincia', 'distrito', 'direccion'];

function status(message, error = false) {
  statusBox.textContent = message;
  statusBox.dataset.error = String(error);
}

operator.addEventListener('change', () => {
  const enabled = operator.value === 'yes' || operator.value === 'no';
  document.querySelector('#record-fields').disabled = !enabled;
  const message = operator.value === 'yes' ? 'Puedes registrar los datos verificados y exportar la lista.'
    : operator.value === 'no' ? 'La consulta indica que no eres miembro de mesa; puedes guardar este resultado con estado “No”.'
    : 'Consulta primero tu condición de miembro de mesa.';
  document.querySelector('#condition').textContent = message;
  status(message);
});

extractButton.addEventListener('click', async () => {
  extractButton.disabled = true;
  try {
    const response = await fetch('/api/onpe/extraer', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: document.querySelector('#onpe-response').value,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo extraer la respuesta ONPE.');
    const record = result.record;
    operator.value = record.miembroMesa ? 'yes' : 'no';
    operator.dispatchEvent(new Event('change'));
    for (const key of fields) document.querySelector(`#${key}`).value = record[key] || '';
    status(`JSON extraído: ${record.cargo || (record.miembroMesa ? 'Miembro de mesa' : 'No es miembro de mesa')}. Verifica los datos antes de guardar.`);
  } catch (error) { status(error.message, true); }
  finally { extractButton.disabled = false; }
});

async function loadRecords() {
  const response = await fetch('/api/registros');
  if (!response.ok) throw new Error('No se pudo leer la lista de registros.');
  const { records } = await response.json();
  const body = document.querySelector('#rows');
  body.replaceChildren();
  for (const record of records) {
    const row = document.createElement('tr');
    for (const key of fields) {
      const cell = document.createElement('td');
      cell.textContent = record[key];
      row.appendChild(cell);
    }
    const action = document.createElement('td');
    const button = document.createElement('button');
    button.textContent = 'Eliminar';
    button.addEventListener('click', async () => {
      if (!confirm(`¿Eliminar el registro del DNI ${record.dni}?`)) return;
      button.disabled = true;
      try {
        const result = await fetch(`/api/registros/${encodeURIComponent(record.dni)}`, { method: 'DELETE' });
        if (!result.ok) throw new Error('No se pudo eliminar el registro.');
        await loadRecords();
        status('Registro eliminado.');
      } catch (error) { status(error.message, true); button.disabled = false; }
    });
    action.appendChild(button);
    row.appendChild(action);
    body.appendChild(row);
  }
  document.querySelector('#count').textContent = `${records.length} registro${records.length === 1 ? '' : 's'}`;
  document.querySelector('#empty').hidden = records.length > 0;
  exportButton.disabled = records.length === 0;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.querySelector('#save');
  button.disabled = true;
  const data = Object.fromEntries(new FormData(form));
  data.confirmed = document.querySelector('#confirmed').checked;
  data.operator_is_member = operator.value === 'yes';
  try {
    const response = await fetch('/api/registros', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo guardar el registro.');
    form.reset();
    await loadRecords();
    status('Registro guardado. Puedes agregar otro DNI o descargar la lista en Excel.');
  } catch (error) { status(error.message, true); }
  finally { button.disabled = false; }
});

exportButton.addEventListener('click', async () => {
  exportButton.disabled = true;
  try {
    const response = await fetch('/exportar.xlsx');
    if (!response.ok) throw new Error('No se pudo exportar la lista. Comprueba que tenga registros.');
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = 'consulta-electoral.xlsx';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    status('Excel generado. Revisa consulta-electoral.xlsx en las descargas de tu navegador.');
  } catch (error) { status(error.message, true); }
  finally { exportButton.disabled = false; }
});

loadRecords().catch((error) => status(error.message, true));

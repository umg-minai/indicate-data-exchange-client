async function callMethod(method) {
    return await fetch('/api/' + method, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    });
}

function showError(message) {
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.textContent = message;
    ['hidden', 'success'].map(function (klass) { statusMessage.classList.remove(klass) })
    statusMessage.classList.add('error');
}

function showSuccessAndRedirect(message) {
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.textContent = message;
    ['hidden', 'error'].map(function (klass) { statusMessage.classList.remove(klass) })
    statusMessage.classList.add('success');

    setTimeout(() => {window.location.href = '/review';}, 2000);
}

async function callMethodAndPresentResult(method, errorMessage) {
    const response = await callMethod(method)
    const data = await response.json();
    if (response.ok) {
        showSuccessAndRedirect(data.message)
    } else {
        showError(data.error || errorMessage);
    }
}

async function performAction(action) {
    const confirmBtn = document.getElementById('confirmBtn');
    const rejectBtn = document.getElementById('rejectBtn');

    confirmBtn.disabled = true;
    confirmBtn.classList.add('busy');
    rejectBtn.disabled = true;

    try {
        await action()
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.classList.remove('busy');
        rejectBtn.disabled = false;
    }
}

async function confirmUpload() {
    performAction(async function() {
        await callMethodAndPresentResult('confirm', 'Upload failed')
    })
}

async function rejectUpload() {
    if (!confirm('Are you sure you want to reject and clear this data?')) {
        return;
    }

    performAction(async function() {
        await callMethodAndPresentResult('reject', 'Rejection failed')
    })
}

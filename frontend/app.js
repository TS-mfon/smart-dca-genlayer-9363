const CONTRACT_ADDRESS = "0x1dC06EaDD445C82810bBe2Ead5564e878c899A4b";
const RPC_URL = "https://studionet.genlayer.com";

let client;
let userAddress;

async function init() {
    if (window.ethereum) {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            userAddress = accounts[0];
            document.getElementById('wallet-status').innerText = `Connected: ${userAddress}`;
            document.getElementById('wallet-status').className = 'badge bg-success';
            document.getElementById('connect-btn').style.display = 'none';
            
            client = new GenLayerClient({ rpcUrl: RPC_URL });
            
            await loadPolicies();
            await loadQueue();
        } catch (error) {
            console.error(error);
            alert("Failed to connect wallet.");
        }
    } else {
        alert("Please install MetaMask!");
    }
}

async function loadPolicies() {
    const tableBody = document.getElementById('policies-tbody');
    tableBody.innerHTML = '<tr><td colspan="7" class="text-center">Loading policies...</td></tr>';
    try {
        const counter = await client.readContract({
            address: CONTRACT_ADDRESS,
            functionName: 'policy_counter',
            args: []
        });
        
        tableBody.innerHTML = '';
        if (counter === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No policies registered yet.</td></tr>';
            return;
        }
        
        for (let i = 1; i <= counter; i++) {
            const rawPolicy = await client.readContract({
                address: CONTRACT_ADDRESS,
                functionName: 'get_policy',
                args: [`POL-${i}`]
            });
            const p = JSON.parse(rawPolicy);
            if (!p.policy_id) continue;
            
            const row = document.createElement('tr');
            let statusBadge = '<span class="badge bg-secondary">' + p.status + '</span>';
            if (p.status === 'Active') statusBadge = '<span class="badge bg-success">Active</span>';
            else if (p.status === 'Paused') statusBadge = '<span class="badge bg-warning text-dark">Paused</span>';
            else if (p.status === 'Rejected' || p.status === 'Blocked') statusBadge = '<span class="badge bg-danger">Blocked</span>';
            
            row.innerHTML = `
                <td>${p.policy_id}</td>
                <td>${p.funding_asset} &rarr; ${p.target_asset_constraints}</td>
                <td>${p.nominal_spend_amount}</td>
                <td>Every ${p.cadence_definition}s</td>
                <td>${statusBadge}</td>
                <td>${p.block_reason || p.reject_reason || '-'}</td>
                <td>
                    ${p.status === 'Active' ? `<button class="btn btn-sm btn-warning me-1" onclick="pausePolicy('${p.policy_id}')">Pause</button>` : ''}
                    ${p.status === 'Paused' ? `<button class="btn btn-sm btn-success me-1" onclick="resumePolicy('${p.policy_id}')">Resume</button>` : ''}
                    ${p.status !== 'Cancelled' ? `<button class="btn btn-sm btn-danger" onclick="cancelPolicy('${p.policy_id}')">Cancel</button>` : ''}
                </td>
            `;
            tableBody.appendChild(row);
        }
    } catch (e) {
        console.error(e);
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading policies.</td></tr>';
    }
}

async function loadQueue() {
    const tableBody = document.getElementById('queue-tbody');
    tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Loading queue...</td></tr>';
    try {
        const rawQueue = await client.readContract({
            address: CONTRACT_ADDRESS,
            functionName: 'get_queue',
            args: []
        });
        const q = JSON.parse(rawQueue);
        
        tableBody.innerHTML = '';
        if (q.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Queue is empty.</td></tr>';
            return;
        }
        
        for (const item of q) {
            const row = document.createElement('tr');
            const nextDue = new Date(item.next_due_at * 1000).toLocaleString();
            const retryDue = item.retry_due_at > 0 ? new Date(item.retry_due_at * 1000).toLocaleString() : '-';
            const qBadge = item.quarantine_flag ? '<span class="badge bg-danger">Quarantined</span>' : '<span class="badge bg-success">Ready</span>';
            
            row.innerHTML = `
                <td>${item.policy_id}</td>
                <td>${nextDue}</td>
                <td>${retryDue}</td>
                <td>${qBadge}</td>
                <td>${item.quarantine_reason || '-'}</td>
            `;
            tableBody.appendChild(row);
        }
    } catch (e) {
        console.error(e);
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading queue.</td></tr>';
    }
}

async function registerPolicy(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('register-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Registering...';
    
    try {
        const fundingAsset = document.getElementById('fundingAsset').value;
        const targetConstraints = document.getElementById('targetConstraints').value;
        const nominalSpend = parseInt(document.getElementById('nominalSpend').value);
        const cadence = parseInt(document.getElementById('cadence').value);
        const slippage = parseInt(document.getElementById('slippage').value);
        const strategy = document.getElementById('strategyProfile').value;
        
        const tx = await client.writeContract({
            address: CONTRACT_ADDRESS,
            functionName: 'register_policy',
            args: [
                userAddress, // owner
                userAddress, // delegate
                fundingAsset,
                targetConstraints,
                cadence,
                nominalSpend,
                nominalSpend * 5, // interval cap
                nominalSpend * 10, // rolling cap
                60, // execution window
                slippage,
                ["Uniswap"], // venue
                strategy,
                "desc-1", // delegation descriptor ID
                Math.floor(Date.now() / 1000)
            ],
            account: userAddress
        });
        
        alert(`Policy Registered! TX: ${tx}`);
        document.getElementById('register-form').reset();
        await loadPolicies();
        await loadQueue();
    } catch (e) {
        console.error(e);
        alert("Failed to register policy: " + e.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Register Policy';
    }
}

async function pausePolicy(policyId) {
    if (!confirm(`Pause policy ${policyId}?`)) return;
    try {
        await client.writeContract({
            address: CONTRACT_ADDRESS,
            functionName: 'pause_policy',
            args: [policyId],
            account: userAddress
        });
        await loadPolicies();
        await loadQueue();
    } catch (e) {
        console.error(e);
        alert(e.message);
    }
}

async function resumePolicy(policyId) {
    if (!confirm(`Resume policy ${policyId}?`)) return;
    try {
        await client.writeContract({
            address: CONTRACT_ADDRESS,
            functionName: 'resume_policy',
            args: [policyId, Math.floor(Date.now() / 1000)],
            account: userAddress
        });
        await loadPolicies();
        await loadQueue();
    } catch (e) {
        console.error(e);
        alert(e.message);
    }
}

async function cancelPolicy(policyId) {
    if (!confirm(`Cancel policy ${policyId} permanently?`)) return;
    try {
        await client.writeContract({
            address: CONTRACT_ADDRESS,
            functionName: 'cancel_policy',
            args: [policyId],
            account: userAddress
        });
        await loadPolicies();
        await loadQueue();
    } catch (e) {
        console.error(e);
        alert(e.message);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('connect-btn').addEventListener('click', init);
    document.getElementById('register-form').addEventListener('submit', registerPolicy);
});

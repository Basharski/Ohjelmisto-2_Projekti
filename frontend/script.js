const API_BASE = 'http://localhost:5000';

let currentState = null;
let currentPlayer = null;

// Initialise pages when DOM is ready.
document.addEventListener('DOMContentLoaded', () => {
  // If character selection buttons are present, set up role selection.
  if (document.querySelector('.select-btn[data-character]')) {
    initSelectRolePage();
  }
  // If the game status area is present, load game state and destinations.
  if (document.getElementById('current-location')) {
    initGamePage();
  }
});


function initSelectRolePage() {
  // Start a new game on page load.
  fetch(`${API_BASE}/start`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      try {
        localStorage.setItem('game_state', JSON.stringify(data.state));
        localStorage.setItem('player', JSON.stringify(data.player));
      } catch (e) {
        console.warn('Failed to persist initial state:', e);
      }
    })
    .catch(err => console.warn('Error starting game:', err));

  // Map English role names to Finnish names expected by the backend.
  const roleMap = { cook: 'kokki', pilot: 'pilotti', fighter: 'taistelija' };

  const buttons = document.querySelectorAll('.select-btn[data-character]');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const engRole = btn.getAttribute('data-character');
      const role = roleMap[engRole] || engRole;
      fetch(`${API_BASE}/choose_role`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role })
      })
        .then(res => {
          if (!res.ok) {
            return res.json().then(data => {
              throw new Error(data.error || 'Failed to choose role');
            });
          }
          return res.json();
        })
        .then(data => {
          try {
            if (data.state) localStorage.setItem('game_state', JSON.stringify(data.state));
            if (data.player) localStorage.setItem('player', JSON.stringify(data.player));
          } catch (e) {
            console.warn('Failed to persist role state:', e);
          }
          // Navigate to the game screen.
          window.location.href = 'game.html';
        })
        .catch(err => {
          alert(`Error choosing character: ${err.message}`);
        });
    });
  });
}

/**
 * Load the saved game state and available destinations on the game page.
 */
function initGamePage() {
  loadStateAndDestinations();
}


function loadStateAndDestinations() {
  try {
    const storedState = localStorage.getItem('game_state');
    const storedPlayer = localStorage.getItem('player');
    currentState = storedState ? JSON.parse(storedState) : null;
    currentPlayer = storedPlayer ? JSON.parse(storedPlayer) : null;
  } catch (e) {
    console.warn('Failed to parse stored state:', e);
    currentState = null;
    currentPlayer = null;
  }

  if (currentState) {
    updateGameUI({ ...currentState, player: currentPlayer });
  }

  fetch(`${API_BASE}/countries`)
    .then(res => {
      if (!res.ok) throw new Error('Failed to fetch countries');
      return res.json();
    })
    .then(destinations => {
      updateDestinations(destinations);
    })
    .catch(err => console.error('Error loading destinations:', err));
}


function updateGameUI(data) {
  if (!data || !data.location || !data.player) return;
  const locName = data.location.name ? `${data.location.name} (${data.location.iso_country})` : '-';
  document.getElementById('current-location').textContent = locName;
  const player = data.player;
  document.getElementById('fuel-value').textContent = player.fuel != null ? player.fuel : '-';
  document.getElementById('food-value').textContent = player.ruoka != null ? player.ruoka : '-';
  document.getElementById('ammo-value').textContent = player.ammo != null ? player.ammo : '-';
  document.getElementById('time-value').textContent = data.time_left != null ? data.time_left : '-';
  document.getElementById('range-value').textContent = data.range_km != null ? (data.range_km + ' km') : '-';
  document.getElementById('hp-value').textContent = player.hp != null ? player.hp : '-';

  const collected = player.rakettiosat || 0;
  for (let i = 1; i <= 4; i++) {
    const el = document.getElementById(`part-${i}`);
    if (!el) continue;
    if (i <= collected) {
      el.classList.add('collected');
    } else {
      el.classList.remove('collected');
    }
  }

  // Display the list of countries where rocket parts remain.
  const partsRemainingEl = document.getElementById('parts-remaining-list');
  if (partsRemainingEl) {
    if (Array.isArray(data.parts) && data.parts.length > 0) {
      partsRemainingEl.textContent = 'Rocket parts remain in: ' + data.parts.join(', ');
    } else {
      partsRemainingEl.textContent = '';
    }
  }
}


function updateDestinations(destinations) {
  const grid = document.getElementById('destinations-grid');
  if (!grid) return;
  grid.innerHTML = '';
  if (!Array.isArray(destinations) || destinations.length === 0) {
    const msg = document.createElement('p');
    msg.textContent = 'No destinations available.';
    grid.appendChild(msg);
    return;
  }
  destinations.forEach(dest => {
    const card = document.createElement('div');
    card.className = 'destination-card';

    // Determine whether the player can fly to this destination.
    // The backend uses a constant fuel cost per flight (30 units), so we
    // check against that instead of the distance when looking at fuel.
    let canFly = true;
    if (currentState && currentPlayer && typeof dest.distance === 'number') {
      const fuelCostPerFlight = 30;
      if ((currentPlayer.fuel ?? 0) < fuelCostPerFlight) canFly = false;
      if (currentState.range_km != null && dest.distance > currentState.range_km) canFly = false;
    }
    if (!canFly) card.classList.add('disabled');

    const title = document.createElement('h4');
    title.textContent = dest.country;
    // If a rocket part remains in this country, show a rocket indicator
    if (currentState && Array.isArray(currentState.parts) && currentState.parts.includes(dest.iso)) {
      const rocketSpan = document.createElement('span');
      rocketSpan.className = 'rocket-indicator';
      rocketSpan.textContent = '🚀';
      title.appendChild(rocketSpan);
    }

    const distanceP = document.createElement('p');
    distanceP.textContent = `${dest.distance.toFixed(1)} km`;
    card.appendChild(title);
    card.appendChild(distanceP);

    const btn = document.createElement('button');
    btn.className = 'fly-btn';
    if (!canFly) {
      btn.disabled = true;
      btn.textContent = 'Cannot fly';
    } else {
      btn.textContent = 'Fly';
      // Pass the country name to the fly function for animation
      btn.addEventListener('click', () => {
        flyToDestination(dest.icao, dest.country);
      });
    }
    card.appendChild(btn);
    grid.appendChild(card);
  });
}

function flyToDestination(icao, country) {
  // Trigger a simple flight animation across the screen
  flightAnimation(country);

  fetch(`${API_BASE}/fly`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ icao })
  })
    .then(res => res.json())
    .then(data => {
      if (data.Error || data.error) {
        alert(data.Error || data.error || 'Flight failed');
      }
      if (data.state) {
        currentState = data.state;
        try { localStorage.setItem('game_state', JSON.stringify(data.state)); } catch (e) {}
      }
      if (data.player) {
        currentPlayer = data.player;
        try { localStorage.setItem('player', JSON.stringify(data.player)); } catch (e) {}
      }
      // Show any server-side messages such as loot, enemy encounters or rocket parts.
      if (Array.isArray(data.messages) && data.messages.length > 0) {
        const msgPanel = document.getElementById('messages-panel');
        if (msgPanel) {
          // Build message content and action buttons.
          msgPanel.innerHTML = data.messages.join('<br>') +
            '<div class="message-actions">' +
            '<button class="msg-ok">OK</button>' +
            '<button class="msg-inv">Inventory</button>' +
            '</div>';
          msgPanel.style.display = 'block';
          // Attach event listeners to the action buttons.
          const okBtn = msgPanel.querySelector('.msg-ok');
          const invBtn = msgPanel.querySelector('.msg-inv');
          if (okBtn) {
            okBtn.addEventListener('click', () => {
              msgPanel.style.display = 'none';
              msgPanel.innerHTML = '';
            });
          }
          if (invBtn) {
            invBtn.addEventListener('click', () => {
              msgPanel.style.display = 'none';
              msgPanel.innerHTML = '';
              // Simulate click on inventory button to open inventory modal.
              const inventoryBtn = document.getElementById('inventory-btn');
              if (inventoryBtn) inventoryBtn.click();
            });
          }
        }
      }
      checkEndConditions();
      loadStateAndDestinations();
    })
    .catch(err => {
      console.error('Error flying:', err);
    });
}


function flightAnimation(country) {
  const overlay = document.getElementById('flight-animation-overlay');
  if (!overlay) return;
  overlay.textContent = `✈️💨 ${country}`;
  // Reset any previous animation
  overlay.style.display = 'block';
  overlay.style.animation = '';
  // Force reflow to restart the animation
  void overlay.offsetWidth;
  // Set the animation property to trigger keyframes for a longer duration
  overlay.style.animation = 'fly-plane 4s ease-in-out forwards';
  // Hide after the animation completes
  setTimeout(() => {
    overlay.style.display = 'none';
    overlay.style.animation = '';
  }, 4000);
}

/**
 * Evaluate victory or game over conditions and alert the user if necessary.
 */
function checkEndConditions() {
  if (!currentState || !currentPlayer) return;
  const state = currentState;
  const player = currentPlayer;

  const partsCollected = player.rakettiosat || 0;
  if (partsCollected >= 4 && state.location && state.location.iso_country === 'FI') {
    alert('🎉 Victory! You collected all 4 rocket parts and returned to Helsinki with ' + state.time_left + ' hours to spare.');
    window.location.href = 'index.html';
    return;
  }

  if (player.fuel != null && player.fuel <= 0) {
    alert('💀 GAME OVER: Out of fuel!\nYou collected ' + partsCollected + '/4 rocket parts.');
    window.location.href = 'index.html';
    return;
  }

  if (player.ruoka != null && player.ruoka <= 0) {
    alert('💀 GAME OVER: Out of food!\nYou collected ' + partsCollected + '/4 rocket parts.');
    window.location.href = 'index.html';
    return;
  }

  if (state.time_left != null && state.time_left <= 0) {
    alert('💀 GAME OVER: Time\'s up!\nYou collected ' + partsCollected + '/4 rocket parts.');
    window.location.href = 'index.html';
    return;
  }
}

// Setup inventory modal interactions once the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const invBtn = document.getElementById('inventory-btn');
  const invModal = document.getElementById('inventory-modal');
  const closeInv = document.getElementById('close-inventory');
  const eatBtn = document.getElementById('eat-food-btn');
  const invDetails = document.getElementById('inventory-details');
  if (invBtn) {
    invBtn.addEventListener('click', () => {
      if (!currentPlayer) return;
      // Populate inventory details
      invDetails.innerHTML =
        'Food: ' + (currentPlayer.ruoka ?? 0) + '<br>' +
        'Fuel: ' + (currentPlayer.fuel ?? 0) + '<br>' +
        'Ammo: ' + (currentPlayer.ammo ?? 0) + '<br>' +
        'HP: ' + (currentPlayer.hp ?? 0) + '/100';
      invModal.style.display = 'block';
    });
  }
  if (closeInv) {
    closeInv.addEventListener('click', () => {
      invModal.style.display = 'none';
    });
  }
  if (eatBtn) {
    eatBtn.addEventListener('click', () => {
      fetch(`${API_BASE}/eat`, {
        method: 'POST'
      })
        .then(res => res.json())
        .then(data => {
          if (data.error || data.Error) {
            alert(data.error || data.Error);
            return;
          }
          if (data.player) {
            currentPlayer = data.player;
            try { localStorage.setItem('player', JSON.stringify(data.player)); } catch (e) {}
          }
          if (data.state) {
            currentState = data.state;
            try { localStorage.setItem('game_state', JSON.stringify(data.state)); } catch (e) {}
          }
          updateGameUI({ ...currentState, player: currentPlayer });
          invModal.style.display = 'none';
        })
        .catch(err => {
          alert('Error eating food');
        });
    });
  }
});
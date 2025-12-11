/*
 * script.js – Final frontend integration script
 *
 * Käyttää Python/Flask-backendiä. Game state ja player-data
 * tallennetaan localStorageen, jotta sivun lataus ei kadota tilaa.
 */

const API_BASE = 'http://localhost:5000';

let currentState = null;
let currentPlayer = null;

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.select-btn[data-character]')) {
    initSelectRolePage();
  }
  if (document.getElementById('current-location')) {
    initGamePage();
  }
});

/**
 * Alustaa hahmon valintasivun ja aloittaa pelin backendissä (/start).
 */
function initSelectRolePage() {
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

  const buttons = document.querySelectorAll('.select-btn[data-character]');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const engRole = btn.getAttribute('data-character');

      // Muutetaan englanninkielinen roolin nimi backendin vaatimalle suomenkieliselle versiolle
      const roleMap = { cook: 'kokki', pilot: 'pilotti', fighter: 'taistelija' };
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
          window.location.href = 'game.html';
        })
        .catch(err => {
          alert(`Error choosing character: ${err.message}`);
        });
    });
  });
}

function initGamePage() {
  loadStateAndDestinations();
}

/**
 * Lataa pelitilan localStoragesta ja hakee kohteet backendistä.
 */
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
    })}
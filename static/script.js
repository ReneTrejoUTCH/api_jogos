// script.js: Lógica del frontend para interactuar con las APIs y actualizar la interfaz

document.addEventListener("DOMContentLoaded", function () {
  // Se asigna el evento click al botón "Buscar"
  document.getElementById("searchButton").addEventListener("click", async function () {
    // Obtener y limpiar el valor ingresado por el usuario
    const query = document.getElementById("searchInput").value.trim();
    if (!query) {
      alert("Ingresa un nombre de juego.");
      return;
    }

    // Insertar spinners en cada sección para indicar que se están cargando los datos
    document.getElementById("results").innerHTML = '<div class="spinner"></div>';
    document.getElementById("priceContainer").innerHTML = '<div class="spinner"></div>';
    document.getElementById("youtubeResults").innerHTML = '<div class="spinner"></div>';
    document.getElementById("twitchResults").innerHTML = '<div class="spinner"></div>';

    try {
      // 1. Consultar la API de RAWG para obtener información del juego
      const gameRes = await fetch(`/gameinfo?query=${encodeURIComponent(query)}`);
      const gameData = await gameRes.json();

      // Si la API devuelve un error, se limpian las demás secciones y se muestra el mensaje
      if (gameData.error) {
        document.getElementById("results").innerHTML = `<p>${gameData.error}</p>`;
        document.getElementById("priceContainer").innerHTML = "<p>No hay ofertas disponibles.</p>";
        document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
        document.getElementById("twitchResults").innerHTML = "<p>No hay streams disponibles.</p>";
        return;
      }

      // Actualizar la sección de resultados con la información del juego
      const gameName = gameData.name; // Nombre oficial obtenido de RAWG
      document.getElementById("results").innerHTML = `
          <h2>${gameName}</h2>
          <img src="${gameData.image}" alt="Game Image" class="game-image"/>
          <p><strong>Descripción:</strong> ${gameData.description}</p>
          <p><strong>Fecha de lanzamiento:</strong> ${gameData.release_date}</p>
          <p><strong>Plataformas:</strong> ${gameData.platforms.join(", ")}</p>
          <p><strong>Rating:</strong> ${gameData.rating}</p>
      `;

      // 2. Consultar la API de CheapShark para obtener ofertas relacionadas
      const priceRes = await fetch(`/search_game?name=${encodeURIComponent(gameName)}`);
      const priceData = await priceRes.json();

      if (priceData.price && priceData.price.length > 0) {
        // Construir la tabla HTML con las ofertas
        let priceHTML = `
          <h3>Precios y Descuentos</h3>
          <table border="1">
            <tr>
              <th>Tienda</th>
              <th>Precio Normal</th>
              <th>Precio Oferta</th>
              <th>Enlace</th>
            </tr>
        `;

        // Recorrer cada oferta y agregar una fila a la tabla
        priceData.price.forEach(deal => {
          priceHTML += `
            <tr>
              <td>${deal.title}</td>
              <td>$${deal.normalPrice}</td>
              <td><strong>$${deal.salePrice}</strong></td>
              <td><a href="${deal.dealLink}" target="_blank">Comprar</a></td>
            </tr>
          `;
        });

        priceHTML += `</table>`;
        // Actualizar el contenedor de precios
        document.getElementById("priceContainer").innerHTML = priceHTML;
      } else {
        document.getElementById("priceContainer").innerHTML = "<p>No hay ofertas disponibles.</p>";
      }

      // 3. Consultar la API de YouTube para obtener videos (trailers o gameplays)
      const ytRes = await fetch(`/youtube?query=${encodeURIComponent(gameName)}`);
      let ytData = {};

      if (!ytRes.ok) {
        document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
        alert("No se encontraron videos de trailers o gameplays específicos para este juego.");
      } else {
        ytData = await ytRes.json();
        if (ytData.videos) {
          // Filtrar videos que contengan el nombre del juego y la palabra "trailer" o "gameplay"
          let validVideos = ytData.videos.filter(video =>
            video.title.toLowerCase().includes(gameName.toLowerCase()) &&
            (video.title.toLowerCase().includes("trailer") || video.title.toLowerCase().includes("gameplay"))
          );

          if (validVideos.length > 0) {
            // Actualizar la sección de videos con los iframes correspondientes
            document.getElementById("youtubeResults").innerHTML = validVideos.map(video => `
              <iframe width="300" height="200" src="${video.embed_url}" frameborder="0" allowfullscreen></iframe>
            `).join('');
          } else {
            document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
            alert("No se encontraron videos de trailers o gameplays específicos para este juego.");
          }
        } else {
          document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
          alert("No se encontraron videos de trailers o gameplays específicos para este juego.");
        }
      }

      // 4. Consultar la API de Twitch para obtener streams en vivo
      const twitchRes = await fetch(`/twitch?game=${encodeURIComponent(gameName)}`);
      const twitchData = await twitchRes.json();

      if (twitchData.data && twitchData.data.length > 0) {
        // Actualizar la sección de streams con la información obtenida
        document.getElementById("twitchResults").innerHTML = twitchData.data.map(stream => `
          <div class="stream">
            <a href="https://www.twitch.tv/${stream.user_name}" target="_blank">
              <img src="${stream.thumbnail_url}" alt="${stream.user_name}" class="stream-thumbnail">
            </a>
            <p><strong>${stream.user_name}</strong> (${stream.viewer_count} viewers)</p>
          </div>
        `).join('');
      } else {
        document.getElementById("twitchResults").innerHTML = "<p>No hay streams disponibles.</p>";
        alert("No se encontraron streams en vivo para este juego.");
      }

    } catch (error) {
      document.getElementById("results").innerHTML = "<p>Error al cargar los datos.</p>";
      console.error("Error fetching data:", error);
    }
  });
});

// evento DOMContentLoaded para asegurarse de que el DOM esté completamente cargado antes de ejecutar el script
// DOM significa Document Object Model, osea el documento HTML
document.addEventListener("DOMContentLoaded", function () {
  // Se asigna el evento click al botón "Buscar"
  document.getElementById("searchButton").addEventListener("click", async function () {
    // Obtener y limpiar el valor ingresado por el usuario
    // trim() elimina los espacios en blanco al principio y al final de la cadena
    // query es la cadena que el usuario ingresó en el campo de búsqueda
    const query = document.getElementById("searchInput").value.trim();
    // si no hay query, muestra alerta
    if (!query) {
      alert("Ingresa un nombre de juego.");
      return;
    }

    // Insertar spinners en cada sección para indicar que se están cargando los datos
    // meramente decorativo
    document.getElementById("results").innerHTML = '<div class="spinner"></div>';
    document.getElementById("priceContainer").innerHTML = '<div class="spinner"></div>';
    document.getElementById("youtubeResults").innerHTML = '<div class="spinner"></div>';
    document.getElementById("twitchResults").innerHTML = '<div class="spinner"></div>';

    try {
  
 ////////////////// Consultar la API de RAWG para obtener información del juego
      // await esperar a que una promesa se resuelva o rechace
      // fetch es la función que se utiliza para hacer solicitudes
      // encodeURIComponent() codifica el nombre del juego para que sea seguro para la URL 
      const gameRes = await fetch(`/gameinfo?query=${encodeURIComponent(query)}`);
      // esperamos a que la respuesta sea convertida a JSON   
      const gameData = await gameRes.json();

      // Si la API devuelve un error, se limpian las demás secciones y se muestra el mensaje en cada seccion
      if (gameData.error) {
        // innerHTML se utiliza para establecer el contenido HTML de un elemento
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

 ////////////////// Consultar la API de CheapShark para obtener ofertas relacionadas

      // Se utiliza el nombre del juego obtenido de RAWG para buscar ofertas
      // Se espera a que se haga la solicitud y se obtenga la respuesta 
      const priceRes = await fetch(`/search_game?name=${encodeURIComponent(gameName)}`);
      // Se espera a que la respuesta sea convertida a JSON
      const priceData = await priceRes.json();

      // si priceData.price es un array y tiene elementos, se construye la tabla HTML  
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
        // priceData.price es un array de objetos que contienen la información de las ofertas
        // por cada oferta, se crea una fila en la tabla con la información correspondiente
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
        // Cerrar la tabla HTML despues del foreach
        priceHTML += `</table>`;
        // Actualizar el contenedor de precios con la tabla generada
        document.getElementById("priceContainer").innerHTML = priceHTML;
      // si no hay ofertas, se muestra un mensaje  
      } else {
        document.getElementById("priceContainer").innerHTML = "<p>No hay ofertas disponibles.</p>";
      }

////////////////// Consultar la API de YouTube para obtener videos (trailers o gameplays)
      // Se utiliza el nombre del juego obtenido de RAWG para buscar videos
      // Se espera a que se haga la solicitud y se obtenga la respuesta

      const ytRes = await fetch(`/youtube?query=${encodeURIComponent(gameName)}`);
      // Inicia ytData como un objeto vacío 
      let ytData = {};

      // si la respuesta no es ok, se muestra un mensaje y una alerta de error
      // ytRes.ok es una propiedad que indica si la respuesta fue exitosa   
      if (!ytRes.ok) {
        document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
        alert("No se encontraron videos de trailers o gameplays específicos para este juego.");
        // si la respuesta es ok
      } else {
        // Se espera a que la respuesta sea convertida a JSON
        ytData = await ytRes.json();
        // Si ytData.videos existe y tiene elementos, se filtran los videos
        // ytData.videos es un array de objetos que contienen la información de los videos
        if (ytData.videos) {
          // Filtrar videos que contengan el nombre del juego y la palabra "trailer" o "gameplay"
          let validVideos = ytData.videos.filter(video =>
            video.title.toLowerCase().includes(gameName.toLowerCase()) &&
            (video.title.toLowerCase().includes("trailer") || video.title.toLowerCase().includes("gameplay"))
          );
         // si hay videos válidos, se construye el HTML para mostrarlos
          // validVideos ya es el array que contiene los videos filtrados 
          if (validVideos.length > 0) {
            // Actualizar la sección de videos con los iframes correspondientes
            // iframe permite incrustar otro documento HTML dentro de la página
            document.getElementById("youtubeResults").innerHTML = validVideos.map(video => `
              <iframe width="300" height="200" src="${video.embed_url}" frameborder="0" allowfullscreen></iframe>
            `).join('');
            // Si no hay videos válidos, se muestra un mensaje  
          } else {
            document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
            alert("No se encontraron videos de trailers o gameplays específicos para este juego.");
          }
        // Si ytData.videos no existe o no tiene elementos, se muestra un mensaje
        } else {
          document.getElementById("youtubeResults").innerHTML = "<p>No se encontraron videos relevantes.</p>";
          alert("No se encontraron videos de trailers o gameplays específicos para este juego.");
        }
      }

////////////////// Consultar la API de Twitch para obtener streams en vivo

       // Se utiliza el nombre del juego obtenido de RAWG para buscar streams
      // Se espera a que se haga la solicitud y se obtenga la respuesta
      const twitchRes = await fetch(`/twitch?game=${encodeURIComponent(gameName)}`);
      //   Se espera a que la respuesta sea convertida a JSON
      const twitchData = await twitchRes.json();

    //  si twitchData.data existe y tiene elementos, se construye el HTML para mostrarlos 
      if (twitchData.data && twitchData.data.length > 0) {
        // Actualizar la sección de streams con la información obtenida
        document.getElementById("twitchResults").innerHTML = twitchData.data.map(stream => `
          <div class="stream">
              <!-- La imagen del stream que redirecciona a la página de Twitch -->
            <a href="https://www.twitch.tv/${stream.user_name}" target="_blank">
              <img src="${stream.thumbnail_url}" alt="${stream.user_name}" class="stream-thumbnail">
            </a>
            <p><strong>${stream.user_name}</strong> (${stream.viewer_count} viewers)</p>
          </div>
        `).join('');
      // si twitchData.data no existe o no tiene elementos, se muestra un mensaje 
      } else {
        document.getElementById("twitchResults").innerHTML = "<p>No hay streams disponibles.</p>";
        alert("No se encontraron streams en vivo para este juego.");
      }

    // si hay un error al cargar los datos, se muestra un mensaje de error
    // y se imprime el error en la consola  
    } catch (error) {
      document.getElementById("results").innerHTML = "<p>Error al cargar los datos.</p>";
      console.error("Error fetching data:", error);
    }
  });
});

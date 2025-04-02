document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("searchButton").addEventListener("click", async function () {
        const query = document.getElementById("searchInput").value;
        if (!query) {
            alert("Ingresa un nombre de juego.");
            return;
        }

        document.getElementById("results").innerHTML = "<p>Cargando...</p>";
        document.getElementById("priceContainer").innerHTML = "<p>Cargando...</p>";
        document.getElementById("youtubeResults").innerHTML = "<p>Cargando...</p>";
        document.getElementById("twitchResults").innerHTML = "<p>Cargando...</p>";

        try {
            // 🔹 Obtener información del juego
            const gameRes = await fetch(`/gameinfo?query=${query}`);
            const gameData = await gameRes.json();

            if (gameData.error) {
                document.getElementById("results").innerHTML = `<p>${gameData.error}</p>`;
                return;
            }

            document.getElementById("results").innerHTML = `
                <h2>${gameData.name}</h2>
                <img src="${gameData.image}" alt="Game Image" class="game-image"/>
                <p><strong>Descripción:</strong> ${gameData.description}</p>
                <p><strong>Fecha de lanzamiento:</strong> ${gameData.release_date}</p>
                <p><strong>Plataformas:</strong> ${gameData.platforms.join(", ")}</p>
                <p><strong>Rating:</strong> ${gameData.rating}</p>
            `;

            // 🔹 Obtener precios del juego
            const priceRes = await fetch(`/search_game?name=${encodeURIComponent(query)}`);
            const priceData = await priceRes.json();

            if (priceData.price && priceData.price.length > 0) {
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
                document.getElementById("priceContainer").innerHTML = priceHTML;
            } else {
                document.getElementById("priceContainer").innerHTML = "<p>No hay ofertas disponibles</p>";
            }

            // 🔹 Obtener videos de YouTube
            const ytRes = await fetch(`/youtube?query=${query}`);
            const ytData = await ytRes.json();

            if (ytData.error) {
                document.getElementById("youtubeResults").innerHTML = `<p>${ytData.error}</p>`;
            } else {
                document.getElementById("youtubeResults").innerHTML = ytData.videos.map(video => `
                    <iframe width="300" height="200" src="${video.embed_url}" frameborder="0" allowfullscreen></iframe>
                `).join('');
            }

            // 🔹 Obtener streams de Twitch
            const twitchRes = await fetch(`/twitch?game=${query}`);
            const twitchData = await twitchRes.json();

            console.log("📺 Respuesta de Twitch API:", twitchData); // Agrega esto para ver la respuesta real

            if (twitchData.error) {
                document.getElementById("twitchResults").innerHTML = `<p>${twitchData.error}</p>`;
            } else if (twitchData.data && twitchData.data.length > 0) {
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
            }




        } catch (error) {
            document.getElementById("results").innerHTML = "<p>Error al cargar los datos.</p>";
            console.error("Error fetching data:", error);
        }
    });
});

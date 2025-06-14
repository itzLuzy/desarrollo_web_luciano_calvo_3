function validarFormulario() {
    const nombre = document.getElementById('nombre');
    const email = document.getElementById('email');
    const errores = [];

    if (!nombre.value.trim()) {
        errores.push("El nombre es obligatorio");
    } 
    else if (nombre.value.length > 200) {
        errores.push("El nombre debe tener máximo 200 caracteres");
    }

    if (!email.value.includes("@")) {
        errores.push("El email no tiene formato válido");
    }

    if (errores.length > 0) {
        alert("Errores:\n" + errores.join("\n"));
        return false;
    }
    return;
}

function mostrarInputRedSocial() {
    const red = document.getElementById("redes").value;
    const idRed = document.getElementById("idRed");
    idRed.style.display = red ? "inline-block" : "none";
}

function mostrarOtroTema() {
    const tema = document.getElementById("tema").value;
    const otro = document.getElementById("otroTema");
    otro.style.display = tema === "otro" ? "inline-block" : "none";
}

function mostrarImagen(src) {
    document.getElementById("grande").src = src;
    document.getElementById("lightbox").style.display = "flex";
}

function cerrarImagen() {
    document.getElementById("lightbox").style.display = "none";
}

function displayTextboxOnCheck(element, method){
    if (element.checked) {
      document.getElementById(method+'_id').style.display = "block";
    } 
    else {
       document.getElementById(method+'_id').style.display = "none";
    }
}

function actualizarComunas(regionSelect) {
    let regionId = regionSelect.value;
    let comunaSelect = document.getElementById('comuna');
    comunaSelect.innerHTML = '<option value="">--Elige una opción--</option>';
    if(regionId == "") {
        return;
    }

    fetch('/get_comunas/' + regionId)
        .then(response => response.json())
        .then(data => {
            data.forEach(comuna => {
                let option = document.createElement('option');
                option.value = comuna.id;
                option.textContent = comuna.nombre;
                comunaSelect.appendChild(option);
            });
        });
}

function resetRegiones() {
    document.getElementById('region').selectedIndex = 0;
}

function cargarComentarios(actividadId) {
    fetch(`/api/comentarios/${actividadId}`)
        .then(r => r.json())
        .then(comentarios => {
            const lista = document.getElementById("comentarios-lista");
            lista.innerHTML = "";
            comentarios.forEach(c => {
                const item = document.createElement("li");
                item.innerHTML = `<strong>${c.nombre}</strong> (${c.fecha}): <br>${c.texto}`;
                lista.appendChild(item);
            });
        });
}

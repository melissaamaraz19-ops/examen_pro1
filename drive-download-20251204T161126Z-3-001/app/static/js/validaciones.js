/**
 * Validaciones Client-Side para Horarios GA
 */

// Validar bloques (bloque_inicio <= bloque_fin)
function validarBloques(formId) {
    const form = document.getElementById(formId) || document.querySelector('form');
    const b1Input = form.querySelector('[name="b1"]') || form.querySelector('[name="bloque_inicio"]');
    const b2Input = form.querySelector('[name="b2"]') || form.querySelector('[name="bloque_fin"]');

    if (!b1Input || !b2Input) return true;

    const b1 = parseInt(b1Input.value);
    const b2 = parseInt(b2Input.value);

    if (isNaN(b1) || isNaN(b2)) {
        alert('❌ Los bloques deben ser números válidos');
        return false;
    }

    if (b1 < 1 || b1 > 8 || b2 < 1 || b2 > 8) {
        alert('❌ Los bloques deben estar entre 1 y 8');
        b1Input.focus();
        return false;
    }

    if (b2 < b1) {
        alert('❌ El bloque final debe ser mayor o igual al bloque inicial');
        b2Input.focus();
        return false;
    }

    // Validar que no exceda 2 bloques (para nuevas restricciones)
    if ((b2 - b1 + 1) > 2) {
        const confirmar = confirm('⚠️ Advertencia: Estás asignando más de 2 bloques consecutivos. Esto podría violar restricciones del GA. ¿Continuar?');
        if (!confirmar) return false;
    }

    return true;
}

// Validar sesiones por semana
function validarSesionesSemana() {
    const input = document.querySelector('[name="sesiones"]');
    if (!input) return true;

    const sesiones = parseInt(input.value);

    if (isNaN(sesiones) || sesiones < 1) {
        alert('❌ Las sesiones por semana deben ser al menos 1');
        input.focus();
        return false;
    }

    if (sesiones > 10) {
        const confirmar = confirm('⚠️ Advertencia: ' + sesiones + ' sesiones por semana es un número alto. ¿Continuar?');
        if (!confirmar) return false;
    }

    return true;
}

// Validar parámetros del GA
function validarParametrosGA() {
    const gens = parseInt(document.querySelector('[name="gens"]')?.value);
    const tam = parseInt(document.querySelector('[name="tam"]')?.value);
    const elite = parseInt(document.querySelector('[name="elite"]')?.value);

    if (isNaN(gens) || gens < 10) {
        alert('❌ Las generaciones deben ser al menos 10');
        return false;
    }

    if (isNaN(tam) || tam < 10) {
        alert('❌ El tamaño de población debe ser al menos 10');
        return false;
    }

    if (isNaN(elite) || elite < 1) {
        alert('❌ El elite debe ser al menos 1');
        return false;
    }

    if (elite >= tam) {
        alert('❌ El elite debe ser menor que el tamaño de población');
        return false;
    }

    // Advertencia para valores muy altos
    if (gens > 200 || tam > 200) {
        const confirmar = confirm('⚠️ Valores altos detectados. Esto podría tardar varios minutos. ¿Continuar?');
        if (!confirmar) return false;
    }

    return true;
}

// Autocompletado inteligente: filtrar materias por turno del grupo
function inicializarFiltrosMaterias() {
    const grupoSelect = document.querySelector('[name="grupo_id"]');
    const materiaSelect = document.querySelector('[name="materia_id"]');

    if (!grupoSelect || !materiaSelect) return;

    // Guardar todas las opciones originales
    const todasMaterias = Array.from(materiaSelect.options);

    grupoSelect.addEventListener('change', function () {
        if (!this.value) return;

        // Obtener turno del grupo seleccionado
        const selectedOption = this.options[this.selectedIndex];
        const grupoText = selectedOption.textContent;
        const turnoLetra = grupoText.charAt(0); // M o V

        // Filtrar materias del mismo turno
        materiaSelect.innerHTML = '';
        todasMaterias.forEach(option => {
            const materiaText = option.textContent;
            const materiaLetra = materiaText.charAt(0);

            if (option.value === '' || materiaLetra === turnoLetra) {
                materiaSelect.appendChild(option.cloneNode(true));
            }
        });
    });
}

// Validar archivo de importación
function validarArchivoImportacion() {
    const archivoInput = document.querySelector('[name="archivo"]');
    const tipoSelect = document.querySelector('[name="tipo"]');

    if (!archivoInput || !tipoSelect) return true;

    if (!tipoSelect.value) {
        alert('❌ Por favor selecciona el tipo de datos a importar');
        tipoSelect.focus();
        return false;
    }

    if (!archivoInput.files || archivoInput.files.length === 0) {
        alert('❌ Por favor selecciona un archivo Excel');
        archivoInput.focus();
        return false;
    }

    const archivo = archivoInput.files[0];
    const extension = archivo.name.split('.').pop().toLowerCase();

    if (!['xlsx', 'xls'].includes(extension)) {
        alert('❌ El archivo debe ser Excel (.xlsx o .xls)');
        archivoInput.value = '';
        return false;
    }

    // Advertir si el archivo es muy grande (>5MB)
    if (archivo.size > 5 * 1024 * 1024) {
        const confirmar = confirm('⚠️ El archivo es muy grande (>5MB). Esto podría tardar. ¿Continuar?');
        if (!confirmar) return false;
    }

    return true;
}

// Inicializar todas las validaciones al cargar
document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ Sistema de validaciones cargado');

    // Inicializar filtros inteligentes
    inicializarFiltrosMaterias();

    // Agregar validación a formularios
    document.querySelectorAll('form').forEach(form => {
        const action = form.getAttribute('action') || '';

        if (action.includes('disponibilidad') || action.includes('reservas')) {
            form.addEventListener('submit', function (e) {
                if (!validarBloques()) {
                    e.preventDefault();
                }
            });
        }

        if (action.includes('plan')) {
            form.addEventListener('submit', function (e) {
                if (!validarSesionesSemana()) {
                    e.preventDefault();
                }
            });
        }

        if (action.includes('generar')) {
            form.addEventListener('submit', function (e) {
                if (!validarParametrosGA()) {
                    e.preventDefault();
                }
            });
        }

        if (action.includes('importar')) {
            form.addEventListener('submit', function (e) {
                if (!validarArchivoImportacion()) {
                    e.preventDefault();
                }
            });
        }
    });
});
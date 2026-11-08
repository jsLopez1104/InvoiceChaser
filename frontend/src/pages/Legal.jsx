import { Footer, Logo } from "../components/Layout";

function Page({ title, children }) {
  return (
    <div>
      <header className="border-b border-border"><div className="mx-auto max-w-3xl px-4 py-3"><Logo /></div></header>
      <article className="mx-auto max-w-3xl space-y-4 px-4 py-10 text-sm leading-relaxed text-muted [&_h2]:mt-6 [&_h2]:text-base [&_h2]:font-medium [&_h2]:text-ink">
        <h1 className="text-2xl font-semibold text-ink">{title}</h1>
        <p className="rounded border border-warn/40 bg-warn/10 px-3 py-2 text-xs text-warn">
          InvoiceChaser es un proyecto de portafolio. Este texto es una plantilla de ejemplo y no constituye asesoría legal.
        </p>
        {children}
      </article>
      <Footer />
    </div>
  );
}

export function Privacy() {
  return (
    <Page title="Política de tratamiento de datos personales">
      <p>Versión 2026-11-08. Elaborada conforme a la Ley 1581 de 2012 y el Decreto 1377 de 2013 (Colombia).</p>
      <h2>Responsable</h2>
      <p>Juan Sebastián López Valencia, desarrollador de InvoiceChaser. Contacto: el correo indicado en el repositorio del proyecto.</p>
      <h2>Datos que recogemos</h2>
      <p>Del usuario: nombre, nombre del negocio, correo y contraseña (guardada cifrada con bcrypt). De los clientes que el usuario registra: nombre, correo y, opcionalmente, teléfono. De las facturas: número, monto y fechas.</p>
      <h2>Finalidad</h2>
      <p>Únicamente gestionar el cobro de facturas: mostrar el estado de la cartera, enviar recordatorios de pago por correo y registrar pagos recibidos. No vendemos ni compartimos datos con terceros con fines comerciales.</p>
      <h2>Encargados</h2>
      <p>Resend (envío de correos) y Wompi (procesamiento de pagos). Los datos de tarjeta nunca pasan por ni se guardan en InvoiceChaser.</p>
      <h2>Datos de terceros</h2>
      <p>El usuario declara que cuenta con autorización de sus clientes para usar sus datos de contacto con fines de cobro.</p>
      <h2>Tus derechos</h2>
      <p>Conocer, actualizar, rectificar y suprimir tus datos, revocar la autorización y presentar quejas ante la Superintendencia de Industria y Comercio. Puedes borrar tu cuenta y todos tus datos en cualquier momento con el botón "Borrar cuenta". Las consultas se responden en máximo 10 días hábiles y los reclamos en 15.</p>
      <h2>Recordatorios de cobro</h2>
      <p>Se envían solo de lunes a viernes de 7:00 a 19:00 y sábados de 8:00 a 15:00 (hora Colombia), nunca domingos ni festivos, y con mínimo 7 días entre cobros de una misma factura vencida, siguiendo el espíritu de la Ley 2300 de 2023.</p>
    </Page>
  );
}

export function Terms() {
  return (
    <Page title="Términos de uso">
      <h2>El servicio</h2>
      <p>InvoiceChaser permite registrar clientes y facturas y envía recordatorios automáticos de pago en nombre del usuario.</p>
      <h2>Responsabilidades del usuario</h2>
      <p>Registrar solo deudas reales, con datos correctos, y contar con autorización de sus clientes para contactarlos. Está prohibido usar el servicio para acosar o enviar mensajes engañosos.</p>
      <h2>Pagos</h2>
      <p>Los pagos se procesan a través de Wompi. InvoiceChaser no almacena datos de tarjetas ni de cuentas bancarias.</p>
      <h2>Cuenta</h2>
      <p>Puedes cerrar tu cuenta cuando quieras desde el panel; se borrarán todos tus datos.</p>
      <h2>Controversias</h2>
      <p>Se rigen por la ley colombiana. Nada en estos términos limita tu derecho como consumidor de acudir a la Superintendencia de Industria y Comercio o a los jueces (Ley 1480 de 2011).</p>
    </Page>
  );
}

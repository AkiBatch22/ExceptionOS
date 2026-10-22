import LoginForm from "./login-form";


export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  const nextPath = next?.startsWith("/") && !next.startsWith("//") ? next : "/";

  return (
    <main className="loginPage">
      <section className="loginCard">
        <p className="eyebrow">Private demonstration</p>
        <h1>ExceptionOS</h1>
        <p className="subtitle">
          Enter the temporary credentials provided with your invitation.
        </p>
        <LoginForm nextPath={nextPath} />
        <p className="privacyNote">
          Use synthetic or deidentified purchase orders only. Demo uploads are
          automatically removed according to the configured retention period.
        </p>
      </section>
    </main>
  );
}

import "../../styles/components/button.css";

function Button({
  children,
  onClick,
  type = "button",
  className = "",
  disabled = false,
}) {
  return (
    <button type={type} onClick={onClick} className={`app-button ${className}`} disabled={disabled}>
      {children}
    </button>
  );
}

export default Button;
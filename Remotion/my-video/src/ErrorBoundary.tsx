import React from "react";

interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage: string;
}

interface ErrorBoundaryProps {
  componentName: string;
  children: React.ReactNode;
}

class ErrorBoundaryClass extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, errorMessage: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#1a1a1a",
            color: "#ff4444",
            fontFamily: "sans-serif",
            padding: 40,
            boxSizing: "border-box",
          }}
        >
          <div style={{ fontSize: 48, marginBottom: 24 }}>⚠️</div>
          <div style={{ fontSize: 32, fontWeight: "bold", marginBottom: 16 }}>
            「{this.props.componentName}」でエラーが出ています
          </div>
          <div
            style={{
              fontSize: 18,
              color: "#aaaaaa",
              maxWidth: 800,
              textAlign: "center",
              wordBreak: "break-all",
            }}
          >
            {this.state.errorMessage}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName: string
): React.FC<P> {
  const WithErrorBoundary: React.FC<P> = (props) => (
    <ErrorBoundaryClass componentName={componentName}>
      <WrappedComponent {...props} />
    </ErrorBoundaryClass>
  );
  WithErrorBoundary.displayName = `withErrorBoundary(${componentName})`;
  return WithErrorBoundary;
}

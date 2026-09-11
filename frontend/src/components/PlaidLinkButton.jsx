import { usePlaidLink } from "react-plaid-link";

function PlaidLinkButton({ linkToken }) {
    const { open, ready } = usePlaidLink({
        token: linkToken,

        onSuccess: async (publicToken, metadata) => {
            console.log("Public token received:", publicToken);

            // Send public token to backend
        },
    });

    return (
        <button
        onClick={() => open()}
        disabled={!ready}
        >
            Link Bank Account
        </button>
    );
}

export default PlaidLinkButton;
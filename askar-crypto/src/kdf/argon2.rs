//! Argon2 key derivation from a password

use crate::{
    error::Error,
    generic_array::typenum::{Unsigned, U16},
};

pub use argon2::{Algorithm, Version};

/// The size of the password salt
pub type SaltSize = U16;

/// The length of the password salt
pub const SALT_LENGTH: usize = SaltSize::USIZE;

/// Standard parameters for 'interactive' level
pub const PARAMS_INTERACTIVE: Params = Params {
    alg: Algorithm::Argon2i,
    version: Version::V0x13,
    mem_cost: 32768,
    time_cost: 4,
};
/// Standard parameters for 'moderate' level
pub const PARAMS_MODERATE: Params = Params {
    alg: Algorithm::Argon2i,
    version: Version::V0x13,
    mem_cost: 131072,
    time_cost: 6,
};

/// Parameters to the argon2 key derivation
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Params {
    alg: Algorithm,
    version: Version,
    mem_cost: u32,
    time_cost: u32,
}

/// Struct wrapping the KDF functionality
#[derive(Clone, Copy, Debug)]
pub struct Argon2;

impl Argon2 {
    /// Derive the key and write it to the provided buffer
    pub fn derive_key(
        password: &[u8],
        salt: &[u8],
        params: Params,
        output: &mut [u8],
    ) -> Result<(), Error> {
        if salt.len() < SALT_LENGTH {
            return Err(err_msg!(Usage, "Invalid salt for argon2i hash"));
        }
        if output.len() > u32::MAX as usize {
            return Err(err_msg!(
                Usage,
                "Output length exceeds max for argon2i hash"
            ));
        }
        let context =
            argon2::Argon2::new(None, params.time_cost, params.mem_cost, 1, params.version)
                .map_err(|_| err_msg!(Unexpected, "Error creating hasher"))?;
        context
            .hash_password_into(params.alg, password, salt, &[], output)
            .map_err(|_| err_msg!(Unexpected, "Error deriving key"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expected() {
        let pass = b"my password";
        let salt = b"long enough salt";
        let mut output = [0u8; 32];
        Argon2::derive_key(pass, salt, PARAMS_INTERACTIVE, &mut output).unwrap();
        assert_eq!(
            output,
            hex!("9ef87bcf828c46c0136a0d1d9e391d713f75b327c6dc190455bd36c1bae33259")
        );
    }
}

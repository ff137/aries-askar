import type { KeyAlgs } from './enums'

type ByteBufferOptions = {
  len: number
  data: Uint8Array
}

type SecretBufferOptions = ByteBufferOptions

type EncryptedBufferOptions = {
  buffer: Uint8Array
  tagPos: number
  noncePos: number
}

type AeadParamsOptions = {
  nonce_length: number
  tag_length: number
}

export class ByteBuffer {
  public len: number
  public data: Uint8Array

  public constructor({ data, len }: ByteBufferOptions) {
    this.data = data
    this.len = len
  }

  public static fromUint8Array(data: Uint8Array): ByteBuffer {
    return new ByteBuffer({ data, len: data.length })
  }
}

export class SecretBuffer {
  public len: number
  public data: Uint8Array

  public constructor({ data, len }: SecretBufferOptions) {
    this.data = data
    this.len = len
  }

  public static fromUint8Array(data: Uint8Array): SecretBuffer {
    return new SecretBuffer({ data, len: data.length })
  }
}

export class EncryptedBuffer {
  private buffer: Uint8Array
  private tagPos: number
  private noncePos: number

  public constructor({ noncePos, tagPos, buffer }: EncryptedBufferOptions) {
    this.buffer = buffer
    this.tagPos = tagPos
    this.noncePos = noncePos
  }

  public get ciphertextAndTag() {
    const p = this.noncePos
    return this.buffer.slice(0, p)
  }

  public get ciphertext() {
    const p = this.tagPos
    return this.buffer.slice(0, p)
  }

  public get nonce() {
    const p = this.noncePos
    return this.buffer.slice(p, this.buffer.length)
  }

  public get tag() {
    const p1 = this.tagPos
    const p2 = this.noncePos
    return this.buffer.slice(p1, p2)
  }

  public get parts() {
    return [this.ciphertext, this.tag, this.nonce]
  }
}

export class AeadParams {
  public nonceLength: number
  public tagLength: number

  public constructor({ nonce_length, tag_length }: AeadParamsOptions) {
    this.nonceLength = nonce_length
    this.tagLength = tag_length
  }
}

export interface ILocalKeyHandle<K = Record<string, unknown>> {
  alg: KeyAlgs
  inner: K
  ephemeral: boolean
}

export type CameraDirection = 'enter' | 'exit'

export type Camera = {
  id: number
  device_ip: string
  login: string
  password?: string
  direction: CameraDirection
  is_active: boolean
}

export type CameraCreateInput = {
  device_ip: string
  login: string
  password: string
  direction: CameraDirection
  is_active?: boolean
}

export type CameraListParams = {
  page?: number
  limit?: number
  search?: string
  device_ip?: string
  login?: string
  direction?: CameraDirection
  is_active?: boolean
}

export type CameraListResponse = {
  total: number
  page: number
  limit: number
  cameras: Camera[]
}

package com.edustory.android.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.edustory.android.data.model.TokenResponse
import com.edustory.android.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginViewModel : ViewModel() {

    private val _loginState = MutableStateFlow<LoginState>(LoginState.Idle)
    val loginState: StateFlow<LoginState> = _loginState.asStateFlow()

    fun login(username: String, password: String) {
        _loginState.value = LoginState.Loading

        val call = RetrofitClient.instance.login(username, password)
        call.enqueue(object : Callback<TokenResponse> {
            override fun onResponse(call: Call<TokenResponse>, response: Response<TokenResponse>) {
                if (response.isSuccessful) {
                    val token = response.body()?.accessToken
                    if (token != null) {
                        _loginState.value = LoginState.Success(token)
                    } else {
                        _loginState.value = LoginState.Error("Empty token received")
                    }
                } else {
                    _loginState.value = LoginState.Error("Login failed: ${response.code()}")
                }
            }

            override fun onFailure(call: Call<TokenResponse>, t: Throwable) {
                _loginState.value = LoginState.Error(t.message ?: "Unknown error")
            }
        })
    }
}

sealed class LoginState {
    object Idle : LoginState()
    object Loading : LoginState()
    data class Success(val token: String) : LoginState()
    data class Error(val message: String) : LoginState()
}

import 'package:get/get.dart';
import '../core/network/api_client.dart';

class InitialBinding extends Bindings {
  @override
  void dependencies() {
    // Initialise Dio singleton before any screen loads
    ApiClient.instance.init();
  }
}